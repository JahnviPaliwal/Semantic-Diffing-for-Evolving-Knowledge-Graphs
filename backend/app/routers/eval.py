"""Evaluation and ablation benchmark API endpoints."""
import json
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from eval.evaluate import main as run_benchmark

from ..core.config import settings
from ..core.database import get_db
from ..core.exceptions import NotFoundException
from ..models.entities import User
from ..schemas.eval import EvalResponse
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/eval", tags=["Evaluation"])


@router.get("/latest", response_model=EvalResponse)
def get_latest_evaluation(current_user: User = Depends(get_current_user)):
    """Retrieve the most recent benchmark evaluation results and ablation metrics."""
    eval_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "results", "eval.json")
    eval_path = os.path.abspath(eval_path)

    if not os.path.exists(eval_path):
        # Run benchmark to produce initial results
        run_benchmark()

    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.post("/run", response_model=EvalResponse)
def execute_evaluation(current_user: User = Depends(get_current_user)):
    """Execute the full evaluation benchmark and return measured precision/recall/F1 and ablation numbers."""
    run_benchmark()
    eval_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "results", "eval.json")
    eval_path = os.path.abspath(eval_path)

    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
