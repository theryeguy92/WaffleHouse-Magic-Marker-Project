import os
import time
import requests
import uuid
import datetime

# Suppress symlink warnings (optional)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Paths for SMV files
SMV_DIR = "/app/smv_files"  # Shared volume between containers
ORDER_VALIDATION_SMV = os.path.join(SMV_DIR, "order_validation.smv")
LLM_RESPONSE_VALIDATION_SMV = os.path.join(SMV_DIR, "llm_response_validation.smv")

# Predefined waffle tokens and their corresponding SMV variables
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

# Mapping from SMV variables to plate markings
plate_markings_map = {
    "jelly_bottom": "Jelly bottom",
    "hashbrowns_top": "Hashbrowns top",
    "oatmeal": "Napkin top",
    "jelly_flipped": "Jelly flipped",
    "apple_jelly_bottom": "Apple jelly bottom",
}

# Function to run nuXmv by waiting for the output file
def run_nuxmv(smv_content, smv_filename_prefix="validation"):
    # Generate a unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    smv_filename = f"{smv_filename_prefix}_{timestamp}_{unique_id}.smv"
    smv_file_path = os.path.join(SMV_DIR, smv_filename)

    # Write the SMV content to the file
    with open(smv_file_path, 'w') as smv_file:
        smv_file.write(smv_content)

    output_file_path = smv_file_path + ".output"

    # Wait for the output file to be produced by the nuxmv container
    max_wait_time = 30  # seconds
    wait_time = 0
    poll_interval = 1  # seconds

    print(f"Waiting for nuXmv to process {os.path.basename(smv_file_path)}...")
    while wait_time < max_wait_time:
        if os.path.exists(output_file_path):
            print(f"Found output file {os.path.basename(output_file_path)}.")
            break
        time.sleep(poll_interval)
        wait_time += poll_interval
    else:
        print("Timeout waiting for nuXmv output.")
        return False

    # Read the output
    with open(output_file_path, "r") as output_file:
        output = output_file.read()

    # Optionally, clean up the output file (keeping the .smv file)
    # os.remove(output_file_path)

    # Check for errors in output
    if "Parser error" in output or "Error" in output or "terminated by a signal" in output:
        print("\nValidation failed due to parsing error.")
        return False
    elif "is false" in output:
        print("\nValidation failed. Counterexamples found.")
        return False
    else:
        print("\nValidation passed.")
        return True

# Function to tokenize user input into SMV variables
def tokenize_to_smv_variables(order):
    smv_vars = {var: "FALSE" for var in waffle_tokens.values()}
    order_lower = order.lower()
    for item, var in waffle_tokens.items():
        if item in order_lower:
            smv_vars[var] = "TRUE"
    return smv_vars

# Function to communicate with the LLM container
def query_llm(prompt):
    try:
        response = requests.post(
            "http://llm:5000/generate/",
            json={"prompt": prompt, "max_length": 100},
        )
        response_data = response.json()
        if "error" in response_data:
            raise Exception(response_data["error"])
        return response_data["generated_text"]
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None

# Function to extract tokens from the LLM's response
def extract_tokens_from_response(response):
    # Extract the Plate Markings and Order from the LLM's response
    plate_markings = []
    order_items = []
    lines = response.strip().splitlines()
    for line in lines:
        if line.startswith("Plate Markings:"):
            # Get the plate markings
            markings_line = line[len("Plate Markings:"):].strip()
            plate_markings = [mark.strip() for mark in markings_line.split(",")]
        elif line.startswith("Order:"):
            # Get the order items
            order_line = line[len("Order:"):].strip()
            order_items = [item.strip() for item in order_line.split(",")]
    return plate_markings, order_items

# Main chatbot function
def waffle_house_chatbot():
    print("Hi! Welcome to Waffle House! Can I take your order?")
    order = input("Your order: ")

    # Tokenize the order into SMV variables
    smv_vars = tokenize_to_smv_variables(order)

    # Read the content of the order validation SMV file (contains TRANS and SPEC)
    with open(ORDER_VALIDATION_SMV, 'r') as f:
        order_validation_content = f.read()

    # Generate SMV content for order validation
    smv_content = "MODULE main\n"
    smv_content += "VAR\n"
    for var in smv_vars:
        smv_content += f"    {var} : boolean;\n"
    smv_content += "\nINIT\n    "
    smv_content += " & ".join([f"{var} = {state}" for var, state in smv_vars.items()]) + ";\n\n"
    # Append the TRANS and SPEC sections
    smv_content += order_validation_content

    # Validate the order using SMV
    print("\nValidating the customer's order...")
    validation_passed = run_nuxmv(smv_content, smv_filename_prefix="order_validation")
    if not validation_passed:
        print("\nOrder validation failed. Unable to proceed.")
        return

    # Get the list of validated items and plate markings
    validated_items = [item for item, var in waffle_tokens.items() if smv_vars[var] == "TRUE"]
    validated_vars = [var for var in smv_vars if smv_vars[var] == "TRUE"]
    plate_markings = [plate_markings_map[var] for var in validated_vars]

    # Construct the LLM prompt using validated tokens
    plate_markings_str = ", ".join(plate_markings)
    order_items_str = ", ".join(validated_items)
    llm_prompt = (
        f"Plate Markings: {plate_markings_str}\n"
        f"Order: {order_items_str}\n"
        f"Respond in the exact format:\n"
        f"Plate Markings: [Plate Markings]\n"
        f"Order: [Order Items]\n"
        f"Use only the tokens provided."
    )

    # Generate the response with the LLM
    print("\nGenerating response with LLM...")
    llm_response = query_llm(llm_prompt)
    if not llm_response:
        print("\nFailed to generate response from LLM.")
        return

    # Extract tokens from the LLM's response
    extracted_plate_markings, extracted_order_items = extract_tokens_from_response(llm_response)

    # Convert extracted tokens into SMV variables
    smv_vars_response = {var: "FALSE" for var in waffle_tokens.values()}
    # For plate markings
    for marking in extracted_plate_markings:
        for var, marking_str in plate_markings_map.items():
            if marking.strip().lower() == marking_str.lower():
                smv_vars_response[var] = "TRUE"
    # For order items
    for item in extracted_order_items:
        for order_item, var in waffle_tokens.items():
            if item.strip().lower() == order_item.lower():
                smv_vars_response[var] = "TRUE"

    # Read the content of the LLM response validation SMV file (which contains only properties)
    with open(LLM_RESPONSE_VALIDATION_SMV, 'r') as f:
        llm_response_validation_content = f.read()

    # Generate SMV content for LLM response validation
    smv_content_response = "MODULE main\n"
    smv_content_response += "VAR\n"
    for var in smv_vars_response:
        smv_content_response += f"    {var} : boolean;\n"

    # Declare additional variables used in llm_response_validation.smv
    smv_content_response += "    acknowledged_order : boolean;\n"
    smv_content_response += "    included_items : boolean;\n"
    smv_content_response += "    explained_plate_markings : boolean;\n"

    # Initialize variables
    smv_content_response += "\nINIT\n    "
    init_vars = [f"{var} = {state}" for var, state in smv_vars_response.items()]
    init_vars += ["acknowledged_order = TRUE", "included_items = FALSE", "explained_plate_markings = FALSE"]
    smv_content_response += " & ".join(init_vars) + ";\n\n"

    # Append the content of llm_response_validation.smv
    smv_content_response += llm_response_validation_content

    # Validate the LLM's response using SMV
    print("\nValidating LLM's response...")
    validation_passed = run_nuxmv(smv_content_response, smv_filename_prefix="llm_response_validation")
    if not validation_passed:
        print("\nValidation failed for LLM's response. Counterexamples found.")
        return

    # Output the LLM's response
    print("\nLLM Response:")
    print(llm_response.strip())

if __name__ == "__main__":
    waffle_house_chatbot()
