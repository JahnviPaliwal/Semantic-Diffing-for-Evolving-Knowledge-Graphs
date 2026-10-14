"""
Diff service computing rich semantic differences and generating JSON/CSV exports.
"""
import csv
import io
import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.semantic_diff.diff_engine import SemanticDiffEngine
from src.semantic_diff.models import ExtractionResult
from src.semantic_diff.summary import SummaryGenerator

from ..core.exceptions import BadRequestException, NotFoundException
from ..models.entities import DiffResultModel, Project, User, Version
from ..schemas.diff import DiffExportResponse, DiffResponse
from .project_service import ProjectService


class DiffService:
    @classmethod
    def compute_diff(
        cls,
        db: Session,
        user: User,
        project_id: int,
        from_version_id: int,
        to_version_id: int,
        groq_api_key: Optional[str] = None,
    ) -> DiffResponse:
        ProjectService.get_project_with_ownership(db, project_id, user)

        v_from = db.query(Version).filter(Version.id == from_version_id, Version.project_id == project_id).first()
        v_to = db.query(Version).filter(Version.id == to_version_id, Version.project_id == project_id).first()

        if not v_from:
            raise NotFoundException(f"Source version with ID {from_version_id} not found.")
        if not v_to:
            raise NotFoundException(f"Target version with ID {to_version_id} not found.")

        if not v_from.extracted_graph or not v_to.extracted_graph:
            raise BadRequestException("One or both versions do not have valid extraction graph data.")

        # Reconstruct ExtractionResult models
        ext_from = ExtractionResult(**v_from.extracted_graph)
        ext_to = ExtractionResult(**v_to.extracted_graph)
        ext_from.version_id = v_from.version_label
        ext_to.version_id = v_to.version_label

        engine = SemanticDiffEngine()
        diff_res = engine.compute_diff(ext_from, ext_to)

        # In-memory ephemeral summarizer; key is NEVER written to DB
        summarizer = SummaryGenerator(api_key=groq_api_key)
        narrative = summarizer.generate_summary(diff_res)
        diff_res.narrative = narrative

        # Persist DiffResultModel in database
        diff_record = DiffResultModel(
            project_id=project_id,
            from_version_id=v_from.id,
            to_version_id=v_to.id,
            changes=diff_res.model_dump(),
            severity_summary=diff_res.severity_summary,
            narrative=narrative,
        )
        db.add(diff_record)
        db.commit()
        db.refresh(diff_record)

        return DiffResponse(
            id=diff_record.id,
            project_id=project_id,
            from_version_id=v_from.id,
            to_version_id=v_to.id,
            from_version_label=v_from.version_label,
            to_version_label=v_to.version_label,
            changes=diff_record.changes,
            severity_summary=diff_record.severity_summary,
            narrative=diff_record.narrative,
            created_at=diff_record.created_at,
        )

    @classmethod
    def get_diff(cls, db: Session, user: User, project_id: int, diff_id: int) -> DiffResponse:
        ProjectService.get_project_with_ownership(db, project_id, user)
        diff_record = db.query(DiffResultModel).filter(
            DiffResultModel.id == diff_id,
            DiffResultModel.project_id == project_id,
        ).first()

        if not diff_record:
            raise NotFoundException(f"Diff record with ID {diff_id} not found.")

        v_from = diff_record.from_version
        v_to = diff_record.to_version

        return DiffResponse(
            id=diff_record.id,
            project_id=diff_record.project_id,
            from_version_id=diff_record.from_version_id,
            to_version_id=diff_record.to_version_id,
            from_version_label=v_from.version_label if v_from else "v1",
            to_version_label=v_to.version_label if v_to else "v2",
            changes=diff_record.changes,
            severity_summary=diff_record.severity_summary,
            narrative=diff_record.narrative,
            created_at=diff_record.created_at,
        )

    @classmethod
    def export_diff(cls, db: Session, user: User, project_id: int, diff_id: int, export_format: str) -> DiffExportResponse:
        diff_data = cls.get_diff(db, user, project_id, diff_id)
        fmt = export_format.lower().strip()

        if fmt == "json":
            content_str = json.dumps(diff_data.model_dump(mode="json"), indent=2)
            filename = f"diff_{diff_data.from_version_label}_to_{diff_data.to_version_label}.json"
            return DiffExportResponse(format="json", filename=filename, content=content_str)

        elif fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Element Type", "Change Type", "Canonical Name", "Previous Name",
                "Severity", "Confidence", "Source Quote", "Chunk Reference", "Rationale"
            ])

            items = diff_data.changes.get("items", [])
            for it in items:
                writer.writerow([
                    it.get("element_type", ""),
                    it.get("change_type", ""),
                    it.get("canonical_name", ""),
                    it.get("previous_name", ""),
                    it.get("severity", ""),
                    it.get("confidence", 1.0),
                    it.get("source_quote", ""),
                    it.get("chunk_reference", ""),
                    it.get("rationale", ""),
                ])

            filename = f"diff_{diff_data.from_version_label}_to_{diff_data.to_version_label}.csv"
            return DiffExportResponse(format="csv", filename=filename, content=output.getvalue())

        else:
            raise BadRequestException(f"Unsupported export format '{export_format}'. Supported: json, csv")
