import os
import subprocess
import requests
from transformers import pipeline

# Suppress symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Paths for .smv files
LLM_RESPONSE_VALIDATION_SMV = "llm_response_validation.smv"
MARKING_VALIDATION_SMV = "marking_validation.smv"

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

# Function to run nuXmv inside the container
def run_nuxmv_in_container(smv_file):
    try:
        # Execute nuXmv inside the `nuxmv` container
        result = subprocess.run(
            ["docker", "exec", "nuxmv", "nuXmv", f"/app/smv_files/{smv_file}"],
            capture_output=True,
            text=True,
        )
        output = result.stdout
        errors = result.stderr

        if errors:
            print(f"[ERROR] nuXmv encountered an error:\n{errors}")
            return False, None

        print(f"[nuXmv OUTPUT]\n{output}")

        if "is false" in output:
            print("\nValidation failed. Counterexamples found.")
            return False, output
        else:
            print("\nValidation passed.")
            return True, output

    except Exception as e:
        print(f"Error running nuXmv: {e}")
        return False, None

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

    # Step 1: Validate the Waffle House setting
    print("\nValidating Waffle House setting...")
    setting_valid, _ = run_nuxmv_in_container(LLM_RESPONSE_VALIDATION_SMV)

    if not setting_valid:
        print("\nWaffle House setting validation failed. Unable to proceed.")
        return

    # Step 2: Tokenize the order for SMV validation
    smv_vars = tokenize_to_smv_variables(order)

    # Step 3: Generate dynamic order validation SMV file
    smv_order_file = "dynamic_order_validation.smv"
    with open(smv_order_file, "w") as smv_file:
        smv_file.write("MODULE main\nVAR\n")
        for var in smv_vars.keys():
            smv_file.write(f"    {var} : boolean;\n")

        smv_file.write("\nINIT\n")
        init_conditions = [f"{var} = {state}" for var, state in smv_vars.items()]
        smv_file.write("    " + " & ".join(init_conditions) + ";\n")

    # Step 4: Validate the order marking
    print("\nValidating order marking...")
    order_valid, validation_output = run_nuxmv_in_container(smv_order_file)

    if not order_valid:
        print("\nOrder validation failed. Please modify your order and try again.")
        return

    # Step 5: Generate response using the LLM
    llm_prompt = (
        f"The customer ordered: {order}\n"
        "Respond as a Waffle House server. Acknowledge the order in a polite way and explain how it will be marked."
    )
    print("\nGenerating response with LLM...")
    llm_response = query_llm(llm_prompt)

    if not llm_response:
        print("\nFailed to generate response from LLM.")
        return

    # Step 6: Validate the response
    print("\nValidating response acknowledgment...")
    response_valid, _ = run_nuxmv_in_container(MARKING_VALIDATION_SMV)

    if not response_valid:
        print("\nResponse validation failed. Please review the LLM's response.")
        return

    # Step 7: Display the validated response
    print("\nLLM Response:")
    print(llm_response.strip())

# Entry point for the script
if __name__ == "__main__":
    waffle_house_chatbot()
