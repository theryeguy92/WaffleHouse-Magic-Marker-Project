import os
import time
import requests

# Suppress symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Paths for .smv files
SMV_DIR = "/app/smv_files"
LLM_RESPONSE_VALIDATION_SMV = "llm_response_validation.smv"
ORDER_ACKNOWLEDGEMENT_SMV = "order_acknowledgement.smv"
MARKING_VALIDATION_SMV = "marking_validation.smv"

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

# Function to run nuXmv by writing to the shared volume
def run_nuxmv(smv_file_name, smv_content=None):
    smv_file_path = os.path.join(SMV_DIR, smv_file_name)

    # If smv_content is provided, write it to the smv_file
    if smv_content is not None:
        with open(smv_file_path, "w") as smv_file:
            smv_file.write(smv_content)
    else:
        # Ensure the smv_file exists
        if not os.path.exists(smv_file_path):
            print(f"SMV file {smv_file_name} does not exist in {SMV_DIR}")
            return False, None

    # Wait for the output file
    output_file_path = smv_file_path + ".output"
    timeout = 60  # Increase timeout if needed
    start_time = time.time()
    while not os.path.exists(output_file_path):
        if time.time() - start_time > timeout:
            print(f"Timeout waiting for nuXmv to process the file: {smv_file_name}")
            return False, None
        time.sleep(1)

    # Read the output
    with open(output_file_path, "r") as output_file:
        output = output_file.read()

    # Check for errors in output
    if "is false" in output:
        print(f"\nValidation failed for {smv_file_name}. Counterexamples found.")
        return False, output
    else:
        print(f"\nValidation passed for {smv_file_name}.")
        return True, output

# Function to communicate with the LLM container
def query_llm(prompt):
    try:
        response = requests.post(
            "http://llm:5000/generate/",
            json={"prompt": prompt, "max_length": 150},
        )
        response_data = response.json()
        if "error" in response_data:
            raise Exception(response_data["error"])
        return response_data["generated_text"]
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None

# Tokenize user input into SMV variables
def tokenize_to_smv_variables(order):
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"
    return smv_vars

# Main chatbot function
def waffle_house_chatbot(order=None):
    if order is None:
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Step 1: Validate the order acknowledgement
    print("\nValidating order acknowledgement...")
    acknowledgement_valid, _ = run_nuxmv(ORDER_ACKNOWLEDGEMENT_SMV)

    if not acknowledgement_valid:
        print("\nOrder acknowledgement validation failed. Unable to proceed.")
        return

    # Step 2: Generate response using the LLM
    llm_prompt = (
        f"The customer ordered: {order}\n"
        "Respond as a Waffle House server. Acknowledge the order in a polite way and explain how it will be marked."
    )
    print("\nGenerating response with LLM...")
    llm_response = query_llm(llm_prompt)

    if not llm_response:
        print("\nFailed to generate response from LLM.")
        return

    # Step 3: Validate the marking after LLM response
    print("\nValidating marking...")
    # Tokenize the order for SMV validation
    smv_vars = tokenize_to_smv_variables(order)

    # Generate dynamic marking validation SMV content
    smv_marking_content = "MODULE main\nVAR\n"
    for var in smv_vars.keys():
        smv_marking_content += f"    {var} : boolean;\n"

    smv_marking_content += "\nINIT\n"
    init_conditions = [f"{var} = {state}" for var, state in smv_vars.items()]
    smv_marking_content += "    " + " & ".join(init_conditions) + ";\n"

    marking_valid, _ = run_nuxmv("dynamic_marking_validation.smv", smv_marking_content)

    if not marking_valid:
        print("\nMarking validation failed. Please review the LLM's response.")
        return

    # Step 4: Display the validated response
    print("\nLLM Response:")
    print(llm_response.strip())

# Entry point for the script
if __name__ == "__main__":
    waffle_house_chatbot()