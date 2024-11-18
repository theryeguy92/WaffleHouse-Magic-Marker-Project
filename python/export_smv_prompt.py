import os

# Predefined waffle tokens and markers
waffle_tokens = {
    "scrambled eggs": "jelly_bottom",
    "hashbrowns": "hashbrowns_top",
    "oatmeal": "oatmeal",
    "wheat toast": "jelly_flipped",
    "raisin toast": "apple_jelly_bottom",
}


# Export function to create SMV file for LLM response validation
def export_llm_response_to_smv(response_text, filename="llm_response_validation.smv"):
    """
    Exports an SMV model for validating an LLM response.

    Parameters:
        response_text (str): The LLM's response to validate.
        filename (str): The name of the SMV file to export.
    """
    with open(filename, 'w') as smv_file:
        smv_file.write("MODULE main\nVAR\n")

        # Declare variables representing key elements in the response
        smv_file.write("    acknowledged_order : boolean;\n")
        smv_file.write("    included_items : boolean;\n")
        smv_file.write("    explained_plate_markings : boolean;\n")

        # Define initial conditions (assuming all start as FALSE)
        smv_file.write("\nINIT\n")
        smv_file.write("    !acknowledged_order & !included_items & !explained_plate_markings;\n")

        # TRANS section: Define transitions based on the response content
        smv_file.write("\nTRANS\n")
        smv_file.write("    next(acknowledged_order) = response_acknowledges_order;\n")
        smv_file.write("    next(included_items) = response_includes_items;\n")
        smv_file.write("    next(explained_plate_markings) = response_explains_plate_markings;\n")

        # Define properties to check (LTL specifications)
        smv_file.write("\n-- Specifications\n")
        smv_file.write("LTLSPEC G (acknowledged_order & included_items & explained_plate_markings);\n")

        # Define DEFINE section to set the conditions based on the response_text
        smv_file.write("\nDEFINE\n")
        smv_file.write(
            f"    response_acknowledges_order := {str('thank you' in response_text.lower() or 'sure' in response_text.lower()).upper()};\n")
        smv_file.write(
            f"    response_includes_items := {str(any(item in response_text.lower() for item in waffle_tokens.keys())).upper()};\n")
        smv_file.write(
            f"    response_explains_plate_markings := {str(any(marker in response_text.lower() for marker in waffle_tokens.values())).upper()};\n")

    print(f"SMV model for LLM response validation exported to {filename}")


# Example usage
if __name__ == "__main__":
    # Example LLM response for testing
    test_response = "Sure! Here's your order: scrambled eggs and hashbrowns. Your plate will be marked with jelly_bottom and hashbrowns_top."

    # Export the SMV file
    export_llm_response_to_smv(test_response)
