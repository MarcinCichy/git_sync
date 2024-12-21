import re
import string

def sanitize_description(description):
    """
    Funkcja do usuwania znaków kontrolnych i nowych linii z opisu repozytorium.
    """
    if description:
        sanitized = ''.join(char for char in description if char in string.printable and char not in ['\n', '\r'])
        # Usunięcie dodatkowych znaków specjalnych, jeśli to konieczne
        sanitized = re.sub(r'[^\x20-\x7E]', '', sanitized)
        return sanitized
    return ""

def sanitize_repo_name(name):
    """
    Przekształca nazwę repozytorium na zgodną z GitHub.
    - Zastępuje spacje myślnikami.
    - Usuwa niedozwolone znaki.
    """
    # Zastąpienie spacji myślnikami
    name = name.replace(' ', '-')
    # Usunięcie wszystkich znaków poza alfanumerycznymi, myślnikami i podkreśleniami
    name = re.sub(r'[^\w\-]', '', name)
    return name
