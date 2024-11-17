import os
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


# Control bot function
def control_bot(order=None):
    """
    Chatbot that processes user orders using an LLM for conversational output
    and prints plate markings along with the LLM response.
    """
    if order is None:  # Only ask for input if no order is provided
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Step 1: Generate an LLM response
    llm_response = llm(f"Take the following Waffle House order: {order}", max_length=50)

    # Step 2: Print the raw LLM response
    print("\nLLM Response:")
    print(llm_response[0]["generated_text"])

    # Step 3: Tokenize user input and create SMV variables
    smv_vars = tokenize_to_smv_variables(order)

    # Step 4: Print order configuration
    print("\nOrder Configuration - Plate Marking:")
    for item, marker in waffle_tokens.items():
        if smv_vars[marker] == "TRUE":
            print(f"- {marker}: {item}")


# Example Usage
if __name__ == "__main__":
    control_bot()  # Run normally
