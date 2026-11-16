import unittest
import uuid
import os
import sys
from pathlib import Path
from fastapi import HTTPException

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import app.models
from app.core.db import Base, engine, SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate
from app.api.routes.projects import list_projects, get_project, create_project, delete_project, export_project_bundle

class TestProjectsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()
        user_uuid = uuid.UUID("99999999-9999-9999-9999-999999999999")
        cls.user = cls.db.query(User).filter(User.id == user_uuid).first()
        if not cls.user:
            cls.user = User(
                id=user_uuid,
                email="testrunner@athena.local",
                name="TestRunner",
                auth_provider="supabase"
            )
            cls.db.add(cls.user)
            cls.db.commit()

        # Clean only dedicated test runner projects
        cls.db.query(Project).filter(Project.user_id == user_uuid).delete()
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_project_lifecycle_and_export(self):
        # 1. Create Project
        proj_in = ProjectCreate(
            title="Unit Test AI Platform",
            problem_statement="Automating product planning with multi-agent orchestration"
        )
        created = create_project(project_in=proj_in, current_user=self.user, db=self.db, trigger_pipeline=False)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.title, "Unit Test AI Platform")
        self.assertEqual(created.status, ProjectStatus.QUEUED)

        # 2. Get Project
        fetched = get_project(project_id=created.id, current_user=self.user, db=self.db)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.title, "Unit Test AI Platform")

        # 3. List Projects
        all_projects = list_projects(current_user=self.user, db=self.db)
        self.assertTrue(any(p.id == created.id for p in all_projects))

        # 4. Export Project Bundle ZIP
        export_resp = export_project_bundle(project_id=created.id, current_user=self.user, db=self.db)
        self.assertEqual(export_resp.media_type, "application/zip")
        self.assertTrue(len(export_resp.body) > 0)

        # 5. Delete Project
        delete_project(project_id=created.id, current_user=self.user, db=self.db)
        deleted = self.db.query(Project).filter(Project.id == created.id).first()
        self.assertIsNone(deleted)

    def test_concurrency_rate_limit_429(self):
        # Create 3 projects (max limit)
        p1 = create_project(ProjectCreate(title="P1", problem_statement="P1"), self.user, self.db, trigger_pipeline=False)
        p2 = create_project(ProjectCreate(title="P2", problem_statement="P2"), self.user, self.db, trigger_pipeline=False)
        p3 = create_project(ProjectCreate(title="P3", problem_statement="P3"), self.user, self.db, trigger_pipeline=False)

        # 4th project must raise HTTP 429
        with self.assertRaises(HTTPException) as ctx:
            create_project(ProjectCreate(title="P4", problem_statement="P4"), self.user, self.db, trigger_pipeline=False)
        self.assertEqual(ctx.exception.status_code, 429)

        # Cleanup
        delete_project(p1.id, self.user, self.db)
        delete_project(p2.id, self.user, self.db)
        delete_project(p3.id, self.user, self.db)

if __name__ == "__main__":
    unittest.main()
