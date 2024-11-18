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

def generate_llm_response(order):
    """
    Generate a polite and contextual LLM response for the given order.
    """
    prompt = f"You are a polite Waffle House server. Respond to this customer order: {order}"
    response = llm(
        prompt,
        max_length=50,
        repetition_penalty=1.2,  # Reduce repetitive patterns
        truncation=True,        # Enable truncation
        pad_token_id=50256      # Pad with EOS token (specific for GPT-like models)
    )
    return response[0]["generated_text"]

def map_plate_markings(order):
    """
    Map the user's order to plate markings based on predefined waffle tokens.
    """
    smv_vars = {token: "FALSE" for token in waffle_tokens.values()}  # Default all to FALSE
    for item, marker in waffle_tokens.items():
        if item in order.lower():
            smv_vars[marker] = "TRUE"
    return smv_vars

def print_plate_markings(smv_vars):
    """
    Display the plate markings in a user-friendly format.
    """
    print("\nPlate Markings:")
    for marker, status in smv_vars.items():
        marker_status = "✅ Placed" if status == "TRUE" else "❌ Not Placed"
        print(f"- {marker}: {marker_status}")

def control_bot(order=None):
    """
    Chatbot that processes user orders using an LLM for conversational output
    and prints plate markings without additional validation.
    """
    if order is None:
        print("Hi! Welcome to Waffle House! Can I take your order?")
        order = input("Your order: ")

    # Generate LLM response
    print("\nLLM Response:")
    response = generate_llm_response(order)
    print(response)

    # Map order to plate markings
    smv_vars = map_plate_markings(order)

    # Print plate markings
    print_plate_markings(smv_vars)

# Example Usage
if __name__ == "__main__":
    control_bot()