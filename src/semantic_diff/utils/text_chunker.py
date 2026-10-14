"""
Overlapping text chunker with character offset tracking and sentence boundary awareness.
"""
from typing import List

from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    chunk_id: int = Field(..., description="0-indexed chunk sequence position")
    text: str = Field(..., description="Chunk content")
    start_char: int = Field(..., description="Starting character offset in the source document")
    end_char: int = Field(..., description="Ending character offset in the source document")


def chunk_text(text: str, chunk_size: int = 2000, chunk_overlap: int = 200) -> List[TextChunk]:
    """
    Split text into overlapping chunks while tracking start and end character offsets.
    If text is shorter than chunk_size, returns a single chunk.
    """
    if not text or not text.strip():
        return []

    if len(text) <= chunk_size:
        return [TextChunk(chunk_id=0, text=text, start_char=0, end_char=len(text))]

    chunks: List[TextChunk] = []
    start = 0
    chunk_id = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # If we are not at the end of the text, look for a sentence/newline break
        if end < text_len:
            # Look backwards from 'end' for punctuation followed by space or newline
            split_candidate = -1
            for punct in [".\n", ".\r\n", ". ", "\n\n", "\n"]:
                pos = text.rfind(punct, start + chunk_size // 2, end)
                if pos != -1:
                    split_candidate = max(split_candidate, pos + len(punct))

            if split_candidate != -1 and split_candidate > start:
                end = split_candidate

        chunk_content = text[start:end]
        chunks.append(
            TextChunk(
                chunk_id=chunk_id,
                text=chunk_content,
                start_char=start,
                end_char=end,
            )
        )
        chunk_id += 1

        if end >= text_len:
            break

        start = max(start + 1, end - chunk_overlap)

    return chunks
