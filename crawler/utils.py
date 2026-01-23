import hashlib

def generate_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()
