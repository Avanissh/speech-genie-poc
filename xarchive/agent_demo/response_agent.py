def generate_text(user_input):
    """
    Generate response text (basic for now)
    """

    text = user_input.lower()

# FIXED
    if any(word in text for word in ["hello", "hi", "hey"]):
        return "Hello! How can I assist you?"

    elif "problem" in text:
        return "I understand your concern. Let me help you."

    elif "thanks" in text:
        return "You're welcome!"

    elif "bye" in text:
        return "Goodbye. Have a great day!"

    else:
        return "I'm here to help."