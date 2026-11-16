import unittest
import uuid
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import app.models
from app.core.db import Base, engine, SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.page import AgentType, Page
from app.schemas.project import ProjectCreate
from app.schemas.page import PageUpdate
from app.api.routes.projects import create_project, delete_project
from app.api.routes.pages import list_project_pages, get_project_page, update_project_page

class TestPagesAPI(unittest.TestCase):
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

        # Create test project
        proj_in = ProjectCreate(
            title="Pages Test Spec Project",
            problem_statement="Testing multi-page specs and living validation blueprint"
        )
        cls.project = create_project(project_in=proj_in, current_user=cls.user, db=cls.db, trigger_pipeline=False)

    @classmethod
    def tearDownClass(cls):
        delete_project(project_id=cls.project.id, current_user=cls.user, db=cls.db)
        cls.db.close()

    def test_pages_by_agent_type(self):
        # 1. Fetch Product Page
        prod_page = get_project_page(
            project_id=self.project.id,
            agent_type=AgentType.PRODUCT,
            current_user=self.user,
            db=self.db
        )
        self.assertEqual(prod_page.agent_type, AgentType.PRODUCT)

        # 2. Fetch Validation Page (Ensures VALIDATION enum works seamlessly)
        val_page = get_project_page(
            project_id=self.project.id,
            agent_type=AgentType.VALIDATION,
            current_user=self.user,
            db=self.db
        )
        self.assertEqual(val_page.agent_type, AgentType.VALIDATION)

        # 3. Update Page Blocks
        page_update = PageUpdate(
            title="Updated Architecture Spec",
            content_json={
                "blocks": [
                    {"id": "b-1", "type": "h1", "content": "Living Blueprint Spec"}
                ]
            }
        )
        # Create page in db first if empty placeholder
        page_record = self.db.query(Page).filter(
            Page.project_id == self.project.id,
            Page.agent_type == AgentType.SYSTEM_DESIGN
        ).first()
        if not page_record:
            page_record = Page(
                project_id=self.project.id,
                agent_type=AgentType.SYSTEM_DESIGN,
                title="System Design",
                content_json={}
            )
            self.db.add(page_record)
            self.db.commit()

        updated = update_project_page(
            project_id=self.project.id,
            agent_type=AgentType.SYSTEM_DESIGN,
            page_in=page_update,
            current_user=self.user,
            db=self.db
        )
        self.assertEqual(updated.title, "Updated Architecture Spec")
        self.assertEqual(updated.version, 2)

if __name__ == "__main__":
    unittest.main()
