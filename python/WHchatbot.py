import os
import subprocess
from transformers import pipeline

# Set environment variable to suppress symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load Hugging Face model for text generation
llm = pipeline("text-generation", model="EleutherAI/gpt-neo-125M")

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

# Base project directory (automatically detected)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(BASE_DIR, "..", "prompts")  # Adjust path to locate prompts folder
NUXMV_PATH = r"C:\Users\Ryan Levey\OneDrive\Bureaublad\vandy_cs\CS 6315\hw3\cs6315_hw03\nuxmv.exe"
SMV_FILE = "llm_response_validation.smv"

# Load prompt from file
def load_prompt(filename):
    """
    Loads a prompt from the specified file in the prompts directory.
    """
    prompt_path = os.path.join(PROMPT_DIR, filename)
    with open(prompt_path, "r") as file:
        return file.read()

# Function to tokenize user input and generate SMV variables
def tokenize_to_smv_variables(order):
    """
    Converts user input into SMV variable assignments.
    """
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}  # Default all to FALSE
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"  # Set token to TRUE if present in the order
    return smv_vars

# Function to validate the response using nuXmv
def validate_with_nuxmv():
    """
    Runs nuXmv to validate the LLM response against the specifications.
    """
    try:
        result = subprocess.run(
            [NUXMV_PATH, SMV_FILE],
            capture_output=True,
            text=True
        )
        if "is true" in result.stdout:
            print("\nnuXmv Validation: Response satisfies all specifications.")
        else:
            print("\nnuXmv Validation: Found counterexample. Response violates specifications.")
            print(result.stdout)
    except Exception as e:
        print("\nError running nuXmv:", e)

# Function to validate the order against SMV variables
def validate_smv(smv_vars):
    """
    Validate SMV variables and generate a response.
    """
    valid_items = [marker for marker, state in smv_vars.items() if state == "TRUE"]
    if not valid_items:
        return "Sorry, I could not understand your order. Please provide a valid order."
    validation_response = "Your order has been validated and prepared as follows:\n"
    validation_response += "\n".join(f"- {marker}: Marked" for marker in valid_items)
    return validation_response

# Chatbot function
def waffle_house_chatbot(order=None):
    """
    Chatbot that processes user orders using an LLM for conversational output,
    validates against SMV variables, and explains plate markings.
    """
    if order is None:  # Only ask for input if no order is provided
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Load the base prompt
    base_prompt = load_prompt("waffle_house_server.txt")

    # Dynamically add customer order to the prompt
    final_prompt = f"{base_prompt}\n\nCustomer Order: \"{order}\""

    # Debugging: Print the final prompt
    print("\n[DEBUG] Final Prompt Sent to LLM:")
    print(final_prompt)

    # Step 1: Generate an LLM response
    llm_response = llm(
        final_prompt,
        max_length=150,  # Increase max_length to allow for longer responses
        truncation=True,
    )

    # Step 2: Post-process the LLM response
    raw_response = llm_response[0]["generated_text"]

    # Strip prompt repetition or redundant sections
    response_start = raw_response.find("Server Response:")
    if response_start != -1:
        processed_response = raw_response[response_start:].strip()
    else:
        processed_response = raw_response.strip()

    # Step 3: Display the processed LLM response
    print("\nLLM Response:")
    print(processed_response)

    # Step 4: Tokenize user input into SMV variables
    smv_vars = tokenize_to_smv_variables(order)

    # Step 5: Validate user order and provide feedback
    validation_feedback = validate_smv(smv_vars)
    print("\nValidation Feedback:")
    print(validation_feedback)

    # Step 6: Run nuXmv validation on the response
    print("\nRunning nuXmv Validation...")
    validate_with_nuxmv()

# Main function
if __name__ == "__main__":
    waffle_house_chatbot()
