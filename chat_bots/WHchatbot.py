import os
import time
import requests
import tempfile

# Suppress symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Paths for SMV files
SMV_DIR = "/app/smv_files"
ORDER_VALIDATION_SMV = "order_validation.smv"  # Existing SMV file
LLM_RESPONSE_VALIDATION_SMV = "llm_response_validation.smv"  # Existing SMV file

# Predefined waffle tokens and their SMV variables
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

# Function to run nuXmv using a temporary SMV file
def run_nuxmv(smv_content):
    # Use a temporary file to write the SMV content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.smv', dir=SMV_DIR) as smv_file:
        smv_file_path = smv_file.name
        smv_file.write(smv_content)

    # Run nuXmv
    output_file_path = smv_file_path + ".output"
    os.system(f"nuxmv {smv_file_path} > {output_file_path}")

    # Read the output
    with open(output_file_path, "r") as output_file:
        output = output_file.read()

    # Clean up temporary files
    os.remove(smv_file_path)
    os.remove(output_file_path)

    # Check for errors in output
    if "is false" in output:
        print(f"\nValidation failed. Counterexamples found.")
        return False
    else:
        print(f"\nValidation passed.")
        return True

# Tokenize user input into SMV variables
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

    # Generate SMV content for order validation
    smv_content = "MODULE main\nVAR\n"
    for var in smv_vars:
        smv_content += f"    {var} : boolean;\n"
    smv_content += "\nINIT\n    "
    smv_content += " & ".join([f"{var} = {state.lower()}" for var, state in smv_vars.items()]) + ";\n"

    # Include the order validation SMV file
    smv_content = f'INCLUDE "{ORDER_VALIDATION_SMV}"\n' + smv_content

    # Validate the order using SMV
    print("\nValidating the customer's order...")
    validation_passed = run_nuxmv(smv_content)
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

    # Generate SMV content for LLM response validation
    smv_content_response = "MODULE main\nVAR\n"
    for var in smv_vars_response:
        smv_content_response += f"    {var} : boolean;\n"
    smv_content_response += "\nINIT\n    "
    smv_content_response += " & ".join([f"{var} = {state.lower()}" for var, state in smv_vars_response.items()]) + ";\n"

    # Include the LLM response validation SMV file
    smv_content_response = f'INCLUDE "{LLM_RESPONSE_VALIDATION_SMV}"\n' + smv_content_response

    # Validate the LLM's response using SMV
    print("\nValidating LLM's response...")
    validation_passed = run_nuxmv(smv_content_response)
    if not validation_passed:
        print("\nValidation failed for LLM's response. Counterexamples found.")
        return

    # Output the LLM's response
    print("\nLLM Response:")
    print(llm_response.strip())

if __name__ == "__main__":
    waffle_house_chatbot()
