import os
import subprocess
from transformers import pipeline

# Suppress symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load Hugging Face model for text generation
llm = pipeline(
    "text-generation",
    model="EleutherAI/gpt-neo-125M",
    device=-1  # Use -1 for CPU, 0 for GPU if available
)

# Paths for nuXmv executable and .smv files
NUXMV_PATH = r"C:\Users\Ryan Levey\OneDrive\Bureaublad\vandy_cs\CS 6315\hw3\cs6315_hw03\nuxmv.exe"
WAFFLE_HOUSE_SMV = "llm_response_validation.smv"

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

response_tokens = {
    "acknowledge_order": "Sure! Here is your order",
    "mention_plates": "This is how I will mark it",
    "valid_phrase_used": "Thanks for ordering at Waffle House"
}

# Function to run nuXmv interactively and capture results
def run_nuxmv_interactively(smv_file):
    try:
        commands = f"""
read_model -i {smv_file}
go
check_ltlspec
quit
"""
        result = subprocess.run(
            [NUXMV_PATH],
            input=commands,
            text=True,
            capture_output=True
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
        print(f"Error running nuXmv interactively: {e}")
        return False, None

# Tokenize user input into SMV variables
def tokenize_to_smv_variables(order):
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"
    return smv_vars

# Generate response validation SMV file
def generate_order_acknowledgement_smv(response):
    smv_file = "order_acknowledgement.smv"
    smv_vars = {token: "FALSE" for token in response_tokens.keys()}

    # Tokenize response to mark relevant variables
    for token, phrase in response_tokens.items():
        if phrase.lower() in response.lower():
            smv_vars[token] = "TRUE"

    with open(smv_file, "w") as smv:
        smv.write("MODULE main\nVAR\n")
        for var in smv_vars:
            smv.write(f"    {var} : boolean;\n")
        smv.write("\nINIT\n")
        init_conditions = [f"{var} = {state}" for var, state in smv_vars.items()]
        smv.write("    " + " & ".join(init_conditions) + ";\n")
        smv.write("\nTRANS\n")
        smv.write("    (acknowledge_order -> valid_phrase_used) &\n")
        smv.write("    (mention_plates -> acknowledge_order) &\n")
        smv.write("    (valid_phrase_used -> next(valid_phrase_used)) &\n")
        smv.write("    (acknowledge_order -> next(acknowledge_order));\n")
        smv.write("\nLTLSPEC G (acknowledge_order -> F valid_phrase_used);\n")
        smv.write("LTLSPEC G (mention_plates -> F acknowledge_order);\n")
    return smv_file

# Chatbot function
def waffle_house_chatbot(order=None):
    if order is None:
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Step 1: Validate the Waffle House setting
    print("\nValidating Waffle House setting...")
    setting_valid, _ = run_nuxmv_interactively(WAFFLE_HOUSE_SMV)

    if not setting_valid:
        print("\nWaffle House setting validation failed. Unable to proceed.")
        return

    # Step 2: Tokenize the order for SMV validation
    smv_vars = tokenize_to_smv_variables(order)

    # Step 3: Export order-specific SMV file for validation
    smv_order_file = "dynamic_order_validation.smv"
    with open(smv_order_file, "w") as smv_file:
        smv_file.write("MODULE main\nVAR\n")
        for var in smv_vars.keys():
            smv_file.write(f"    {var} : boolean;\n")

        smv_file.write("\nINIT\n")
        init_conditions = [f"{var} = {state}" for var, state in smv_vars.items()]
        smv_file.write("    " + " & ".join(init_conditions) + ";\n")

        smv_file.write("\nTRANS\n")
        smv_file.write("    (jelly_bottom -> scrambled_eggs) &\n")
        smv_file.write("    (hashbrowns_top -> (scrambled_eggs & !grits)) &\n")
        smv_file.write("    (oatmeal -> (napkin_top & brown_sugar_top));\n")

    print("\n[DEBUG] Generated dynamic_order_validation.smv:")
    with open(smv_order_file, "r") as smv_debug_file:
        print(smv_debug_file.read())

    # Step 4: Validate the order marking
    print("\nValidating order marking...")
    order_valid, validation_output = run_nuxmv_interactively(smv_order_file)

    if not order_valid:
        print("\nOrder validation failed. Please modify your order and try again.")
        return

    # Step 5: Generate LLM response
    llm_prompt = (
        f"The customer ordered: {order}\n"
        "Respond as a Waffle House server. Acknowledge the order in a polite way and explain how it will be marked."
    )
    print("\nGenerating response with LLM...")
    llm_response = llm(llm_prompt, max_length=150, truncation=True)
    response_text = llm_response[0]["generated_text"]

    # Validate response
    print("\nValidating response acknowledgment...")
    response_valid, _ = run_nuxmv_interactively(generate_order_acknowledgement_smv(response_text))

    if not response_valid:
        print("\nResponse validation failed. Please review the LLM's response.")
        return

    # Display the validated response
    print("\nLLM Response:")
    print(response_text.strip())

# Main function
if __name__ == "__main__":
    waffle_house_chatbot()