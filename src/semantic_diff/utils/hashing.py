"""
Cryptographic hashing utility for caching document extractions and graph states.
"""
import hashlib


def compute_text_hash(text: str) -> str:
    """Compute a SHA-256 digest for input text after normalizing whitespace."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
