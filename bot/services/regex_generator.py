import re

def generate_smart_regex(word: str) -> str:
    """
    Generates a robust regex pattern for a given word, handling:
    - Leetspeak (e.g., a -> @, 4; e -> 3)
    - Mixed case
    - Flexible separators (spaces, dots, underscores)
    - Latin/Cyrillic homoglyphs
    """
    
    # Map of characters to their regex character class including lookalikes
    char_map = {
        'a': '[aа@4]', 'а': '[aа@4]',
        'b': '[bв6]', 'в': '[bв6]',
        'c': '[cсk]', 'с': '[cсk]', 'k': '[kкc]', 'к': '[kкc]',
        'd': '[dд]', 'д': '[dд]',
        'e': '[eе3]', 'е': '[eе3]',
        'f': '[fф]', 'ф': '[fф]',
        'g': '[gjg]',
        'h': '[hн]', 'н': '[hн]',
        'i': '[i1!|]', 
        'l': '[l1!|]',
        'm': '[mм]', 'м': '[mм]',
        'n': '[nп]', 'п': '[nп]',
        'o': '[oо0]', 'о': '[oо0]',
        'p': '[pр]', 'р': '[pр]',
        'r': '[rг]', 'г': '[rг]',
        's': '[s$5]',
        't': '[tт7]', 'т': '[tт7]',
        'u': '[uи]', 'и': '[uи]',
        'v': '[v]',
        'w': '[wш]', 'ш': '[wш]',
        'x': '[xх]', 'х': '[xх]',
        'y': '[yу]', 'у': '[yу]',
        'z': '[z3]',
        # Add more as needed
    }

    pattern = ""
    for i, char in enumerate(word.lower()):
        # Get the character class or escape the character if it's special
        char_class = char_map.get(char, re.escape(char))
        
        pattern += char_class
        
        # Add flexible separator after each character except the last one
        if i < len(word) - 1:
            pattern += r"\s*[\W_]*\s*"

    return pattern
