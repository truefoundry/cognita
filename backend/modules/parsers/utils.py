def contains_text(text):
    # Check if the token contains at least one alphanumeric character
    return any(char.isalnum() for char in text)
