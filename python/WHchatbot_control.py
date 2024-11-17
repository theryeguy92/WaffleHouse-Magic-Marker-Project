import os
from transformers import pipeline

# Suppress symlink warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load Hugging Face model for text generation with adjustments for device
llm = pipeline(
    "text-generation",
    model="EleutherAI/gpt-neo-125M",
    device=-1  # Use -1 for CPU, or 0 for GPU if available
)

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}

# Function to process user input and generate plate markings
def control_bot(order=None):
    """
    Chatbot that processes user orders using an LLM for conversational output
    and prints plate markings without additional validation.
    """
    if order is None:
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Step 1: Generate an LLM response with proper settings
    llm_response = llm(
        f"Take the following Waffle House order: {order}",
        max_length=50,
        repetition_penalty=1.2,  # Reduce repetitive patterns
        truncation=True,        # Explicitly enable truncation
        pad_token_id=50256      # Pad with EOS token (specific for GPT-like models)
    )
    print("\nLLM Response:")
    print(llm_response[0]["generated_text"])

    # Step 2: Map order to plate markings
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}  # Default all to FALSE
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"

    # Step 3: Print how the plate is marked
    print("\nPlate Markings:")
    for marker, status in smv_vars.items():
        print(f"- {marker}: {'Placed' if status == 'TRUE' else 'Not Placed'}")

# Example Usage
if __name__ == "__main__":
    control_bot()