"""
Project domain service managing document families, ownership checks, and timelines.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.semantic_diff.models import ExtractionResult
from src.semantic_diff.temporal import TemporalKnowledgeGraph

from ..core.exceptions import ForbiddenException, NotFoundException
from ..models.entities import Project, User, Version
from ..schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from ..schemas.version import VersionResponse


class ProjectService:
    @staticmethod
    def get_project_with_ownership(db: Session, project_id: int, user: User) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundException(f"Project with ID {project_id} not found.")
        if project.user_id != user.id and not user.is_superuser:
            raise ForbiddenException("You do not have permission to access this project.")
        return project

    @staticmethod
    def create_project(db: Session, user: User, project_in: ProjectCreate) -> Project:
        project = Project(
            user_id=user.id,
            name=project_in.name,
            description=project_in.description,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def list_projects(db: Session, user: User) -> List[Dict[str, Any]]:
        projects = db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()
        result = []
        for p in projects:
            p_dict = {
                "id": p.id,
                "user_id": p.user_id,
                "name": p.name,
                "description": p.description,
                "version_count": len(p.versions),
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            result.append(p_dict)
        return result

    @classmethod
    def get_project_detail(cls, db: Session, user: User, project_id: int) -> Dict[str, Any]:
        project = cls.get_project_with_ownership(db, project_id, user)
        version_list = []
        for v in project.versions:
            graph_data = v.extracted_graph or {}
            entities = graph_data.get("entities", [])
            relations = graph_data.get("relations", [])
            version_list.append(
                VersionResponse(
                    id=v.id,
                    project_id=v.project_id,
                    version_num=v.version_num,
                    version_label=v.version_label,
                    filename=v.filename,
                    doc_hash=v.doc_hash,
                    status=v.status,
                    node_count=len(entities),
                    edge_count=len(relations),
                    created_at=v.created_at,
                    extracted_graph=v.extracted_graph,
                )
            )

        return {
            "id": project.id,
            "user_id": project.user_id,
            "name": project.name,
            "description": project.description,
            "version_count": len(project.versions),
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "versions": version_list,
        }

    @classmethod
    def update_project(cls, db: Session, user: User, project_id: int, project_in: ProjectUpdate) -> Project:
        project = cls.get_project_with_ownership(db, project_id, user)
        if project_in.name is not None:
            project.name = project_in.name
        if project_in.description is not None:
            project.description = project_in.description
        db.commit()
        db.refresh(project)
        return project

    @classmethod
    def delete_project(cls, db: Session, user: User, project_id: int) -> None:
        project = cls.get_project_with_ownership(db, project_id, user)
        db.delete(project)
        db.commit()

    @classmethod
    def get_timeline(cls, db: Session, user: User, project_id: int) -> Dict[str, Any]:
        """Construct multi-version temporal knowledge graph and timeline for project."""
        project = cls.get_project_with_ownership(db, project_id, user)
        t_graph = TemporalKnowledgeGraph()

        extractions = []
        for v in project.versions:
            if v.extracted_graph:
                try:
                    ext = ExtractionResult(**v.extracted_graph)
                    ext.version_id = v.version_label
                    extractions.append(ext)
                except Exception:
                    pass

        t_graph.build_from_versions(extractions)
        return t_graph.to_dict()
