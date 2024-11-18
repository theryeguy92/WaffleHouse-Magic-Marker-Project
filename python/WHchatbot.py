import os
import subprocess
from transformers import pipeline

# Set environment variable to suppress symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load Hugging Face model for text generation
llm = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")

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

# Function to run nuXmv interactively and capture results
def run_nuxmv_interactively(smv_file):
    """
    Run nuXmv interactively and perform model checking for LTL specifications.
    """
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

        # Print output and errors for debugging
        if errors:
            print(f"[ERROR] nuXmv encountered an error:\n{errors}")
            return False

        print(f"[nuXmv OUTPUT]\n{output}")

        if "is false" in output:
            print("\nValidation failed. Counterexamples found.")
            return False
        else:
            print("\nValidation passed.")
            return True

    except Exception as e:
        print(f"Error running nuXmv interactively: {e}")
        return False

# Function to tokenize user input into SMV variables
def tokenize_to_smv_variables(order):
    """
    Converts user input into SMV variable assignments for plate markings.
    """
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}  # Default all to FALSE
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"  # Set token to TRUE if present in the order
    return smv_vars

# Chatbot function
def waffle_house_chatbot(order=None):
    """
    Chatbot that validates both the Waffle House setting and order marking
    using .smv files and confirms the order if both validations pass.
    """
    if order is None:  # Only ask for input if no order is provided
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Step 1: Validate the Waffle House setting
    print("\nValidating Waffle House setting...")
    setting_valid = run_nuxmv_interactively(WAFFLE_HOUSE_SMV)

    if not setting_valid:
        print("\nWaffle House setting validation failed. Unable to proceed.")
        return

    # Step 2: Tokenize the order for SMV validation
    smv_vars = tokenize_to_smv_variables(order)

    # Step 3: Export order-specific SMV file for validation
    smv_order_file = "dynamic_order_validation.smv"
    with open(smv_order_file, "w") as smv_file:
        smv_file.write("MODULE main\nVAR\n")

        # Declare all variables from waffle_tokens
        for var in smv_vars.keys():
            smv_file.write(f"    {var} : boolean;\n")

        # Add missing variables needed for rules
        additional_vars = ["scrambled_eggs", "grits", "napkin_top", "brown_sugar_top"]
        for var in additional_vars:
            smv_file.write(f"    {var} : boolean;\n")

        # INIT section reflecting user input and ensuring logical dependencies
        smv_file.write("\nINIT\n")
        init_conditions = []

        # Set variables based on user input
        for var, state in smv_vars.items():
            init_conditions.append(f"{var} = {state}")

        # Add logical dependencies
        if smv_vars.get("hashbrowns_top") == "TRUE":
            init_conditions.append("scrambled_eggs = TRUE")
            init_conditions.append("grits = FALSE")
        else:
            init_conditions.append("scrambled_eggs = FALSE")
            init_conditions.append("grits = FALSE")

        if smv_vars.get("oatmeal") == "TRUE":
            init_conditions.append("napkin_top = TRUE")
            init_conditions.append("brown_sugar_top = TRUE")
        else:
            init_conditions.append("napkin_top = FALSE")
            init_conditions.append("brown_sugar_top = FALSE")

        smv_file.write("    " + " & ".join(init_conditions) + ";\n")

        # TRANS section enforcing rules from generated_wafflehouse.smv
        smv_file.write("\nTRANS\n")
        smv_file.write("    (jelly_bottom -> scrambled_eggs) &\n")
        smv_file.write("    (hashbrowns_top -> (scrambled_eggs & !grits)) &\n")
        smv_file.write("    (oatmeal -> (napkin_top & brown_sugar_top)) &\n")
        smv_file.write("    (!hashbrowns_top | (scrambled_eggs & !grits)) &\n")
        smv_file.write("    (!oatmeal | (napkin_top & brown_sugar_top)) &\n")
        smv_file.write("    (!scrambled_eggs | jelly_bottom | hashbrowns_top) &\n")
        smv_file.write("    !(hashbrowns_top & grits) &\n")
        smv_file.write("    !(oatmeal & jelly_flipped) &\n")
        smv_file.write("    !(scrambled_eggs & grits);\n")

    # Debugging: Print the generated SMV file for inspection
    print("\n[DEBUG] Generated dynamic_order_validation.smv:")
    with open(smv_order_file, "r") as smv_debug_file:
        print(smv_debug_file.read())

    # Step 4: Validate the order marking using nuXmv
    print("\nValidating order marking...")
    order_valid = run_nuxmv_interactively(smv_order_file)

    if not order_valid:
        print("\nOrder validation failed. Please modify your order and try again.")
        return

    # Step 5: Generate LLM response
    print("\nBoth validations passed. Generating response...")
    llm_prompt = (
        "You are a friendly Waffle House server. Respond politely, with some enthusiasm, to the customer's order.\n\n"
        "Customer Order: \"{order}\"\nServer Response:"
    )

    llm_response = llm(llm_prompt.format(order=order), max_length=150, truncation=True)
    # Clean up the response
    processed_response = (
        llm_response[0]["generated_text"]
        .split("Server Response:")[1]
        .strip()
    )

    # Display the LLM response
    print("\nLLM Response:")
    print(f"Server Response: {processed_response}")

# Main function
if __name__ == "__main__":
    waffle_house_chatbot()