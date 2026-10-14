"""Pydantic schemas for benchmark evaluation."""
from typing import Any, Dict, List

from pydantic import BaseModel


class EvalResponse(BaseModel):
    benchmark_summary: Dict[str, Any]
    pairs: List[Dict[str, Any]]
