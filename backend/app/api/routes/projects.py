import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_db_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.agent_run import AgentRun
from app.schemas.project import Project as ProjectSchema, ProjectCreate, ProjectUpdate
from app.workers.tasks import run_agentic_pipeline

router = APIRouter()

@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
    trigger_pipeline: bool = True
):
    """
    Creates a new project and triggers the background multi-agent orchestrator.
    """
    # Blueprint Section 7: Enforce rate limit (max 3 concurrent pipeline executions per user)
    active_runs = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.status.in_([ProjectStatus.QUEUED, ProjectStatus.PROCESSING])
    ).count()
    if active_runs >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum of 3 concurrent pipeline executions reached. Please wait for an active project to complete."
        )

    project = Project(
        user_id=current_user.id,
        title=project_in.title,
        problem_statement=project_in.problem_statement,
        status=ProjectStatus.QUEUED
    )
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        
        if trigger_pipeline:
            # Trigger async pipeline worker task (Celery with thread fallback for non-docker/local dev)
            from app.core.config import settings
            if settings.DEV_MODE:
                import threading
                threading.Thread(
                    target=run_agentic_pipeline,
                    args=(str(project.id), project.problem_statement),
                    daemon=True
                ).start()
            else:
                try:
                    run_agentic_pipeline.delay(str(project.id), project.problem_statement)
                except Exception:
                    import threading
                    threading.Thread(
                        target=run_agentic_pipeline,
                        args=(str(project.id), project.problem_statement),
                        daemon=True
                    ).start()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database execution failed: {str(e)}"
        )
        
    return project

@router.get("/", response_model=List[ProjectSchema])
def list_projects(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all projects owned by the logged-in user.
    """
    return db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves details for a single project owned by the user.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it"
        )
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a project and all its cascading entities (pages, canvas states).
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it"
        )
        
    try:
        db.delete(project)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
    return None

@router.get("/{project_id}/status")
def get_project_status_stream(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) endpoint to stream real-time pipeline status updates
    including individual agent execution steps.
    """
    # Enforce access checks before creating connection
    project_exists = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project workspace not found"
        )

    async def event_generator():
        # Clean session per thread loop
        loop_db = Session(bind=db.bind)
        try:
            while True:
                proj = loop_db.query(Project).filter(Project.id == project_id).first()
                if not proj:
                    yield "event: error\ndata: Project deleted\n\n"
                    break
                
                # Fetch latest agent runs tracking data
                runs = loop_db.query(AgentRun).filter(AgentRun.project_id == project_id).order_by(AgentRun.created_at.asc()).all()
                agent_runs_payload = [
                    {
                        "agent_type": r.agent_type,
                        "status": r.status,
                        "tokens_used": r.tokens_used,
                        "latency_ms": r.latency_ms
                    } for r in runs
                ]
                
                state_data = {
                    "project_id": str(project_id),
                    "status": proj.status,
                    "agent_runs": agent_runs_payload
                }
                
                yield f"event: status_update\ndata: {json.dumps(state_data)}\n\n"
                
                if proj.status in [ProjectStatus.DONE, ProjectStatus.FAILED]:
                    break
                    
                await asyncio.sleep(2)
        finally:
            loop_db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _generate_canvas_svg(nodes: list, edges: list, title: str) -> str:
    width = 1100
    height = 700
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background:#0f172a;font-family:ui-sans-serif,system-ui,sans-serif;">',
        f'<text x="40" y="50" fill="#f8fafc" font-size="22" font-weight="bold">{title} - Architecture Graph</text>',
        '<defs>',
        '  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 0 L 10 5 L 0 10 z" fill="#818cf8"/>',
        '  </marker>',
        '</defs>'
    ]

    node_pos = {}
    for node in nodes:
        nid = str(node.get("id"))
        pos = node.get("position", {})
        x = float(pos.get("x", 100)) + 60
        y = float(pos.get("y", 100)) + 60
        node_pos[nid] = (x, y)
        label = str(node.get("data", {}).get("label") or nid)
        shape = node.get("data", {}).get("shape", "rect")
        bg = "#1e1b4b" if shape == "db" else "#1e293b"
        border = "#818cf8" if shape == "db" else "#38bdf8"

        svg.append(f'<rect x="{x}" y="{y}" width="160" height="60" rx="8" fill="{bg}" stroke="{border}" stroke-width="2"/>')
        clean_label = label[:24].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg.append(f'<text x="{x + 80}" y="{y + 35}" fill="#f8fafc" font-size="12" font-weight="500" text-anchor="middle">{clean_label}</text>')

    for edge in edges:
        s = str(edge.get("source"))
        t = str(edge.get("target"))
        if s in node_pos and t in node_pos:
            x1, y1 = node_pos[s]
            x2, y2 = node_pos[t]
            svg.append(f'<line x1="{x1 + 80}" y1="{y1 + 60}" x2="{x2 + 80}" y2="{y2}" stroke="#818cf8" stroke-width="2" marker-end="url(#arrow)"/>')

    svg.append('</svg>')
    return "\n".join(svg)


@router.get("/{project_id}/export")
def export_project_bundle(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Blueprint Section 2 & 5: Exports the entire project plan, specifications,
    and React Flow systems architecture as a downloadable ZIP archive.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models.page import Page
    from app.models.canvas import CanvasState
    import io
    import json
    import zipfile
    from fastapi.responses import Response

    pages = db.query(Page).filter(Page.project_id == project_id).all()
    canvas = db.query(CanvasState).filter(CanvasState.project_id == project_id).first()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zip_file:
        readme_content = f"# {project.title}\n\n"
        readme_content += f"**Problem Statement:**\n{project.problem_statement}\n\n"
        readme_content += f"**Status:** {project.status}\n"
        readme_content += f"**Created At:** {project.created_at.isoformat()}\n"
        zip_file.writestr("README.md", readme_content)

        for page in pages:
            agent_slug = page.agent_type.value if hasattr(page.agent_type, "value") else str(page.agent_type)
            fname = f"{agent_slug}.md"
            md_lines = [f"# {page.title}\n"]
            content = page.content_json or {}

            if "blocks" in content and isinstance(content["blocks"], list):
                for b in content["blocks"]:
                    btype = b.get("type", "paragraph")
                    btext = b.get("content", "")
                    if btype == "h1":
                        md_lines.append(f"# {btext}\n")
                    elif btype == "h2":
                        md_lines.append(f"## {btext}\n")
                    elif btype == "h3":
                        md_lines.append(f"### {btext}\n")
                    elif btype == "bullet_list":
                        md_lines.append(f"* {btext}")
                    elif btype == "todo":
                        check = "x" if b.get("checked") else " "
                        md_lines.append(f"- [{check}] {btext}")
                    elif btype == "callout":
                        md_lines.append(f"> 💡 {btext}\n")
                    else:
                        md_lines.append(f"{btext}\n")
            else:
                for k, v in content.items():
                    md_lines.append(f"## {k.replace('_', ' ').title()}\n")
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                item_str = ", ".join(f"{ik}: {iv}" for ik, iv in item.items())
                                md_lines.append(f"* {item_str}")
                            else:
                                md_lines.append(f"* {item}")
                    elif isinstance(v, dict):
                        for dk, dv in v.items():
                            md_lines.append(f"* **{dk}**: {dv}")
                    else:
                        md_lines.append(f"{v}\n")
                    md_lines.append("")

            zip_file.writestr(f"specifications/{fname}", "\n".join(md_lines))

        if canvas and canvas.canvas_json:
            zip_file.writestr("architecture/canvas.json", json.dumps(canvas.canvas_json, indent=2))
            nodes = canvas.canvas_json.get("nodes", [])
            edges = canvas.canvas_json.get("edges", [])
            svg_content = _generate_canvas_svg(nodes, edges, project.title)
            zip_file.writestr("architecture/system_diagram.svg", svg_content)

    buf.seek(0)
    slug = "".join(c if c.isalnum() else "_" for c in project.title.lower())[:30]
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{slug}_athena_export.zip"'}
    )


@router.get("/{project_id}/canvas/export")
def export_canvas_svg(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Blueprint Section 2: Returns the static SVG render of the React Flow canvas diagram.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models.canvas import CanvasState
    from fastapi.responses import Response

    canvas = db.query(CanvasState).filter(CanvasState.project_id == project_id).first()
    nodes = canvas.canvas_json.get("nodes", []) if canvas and canvas.canvas_json else []
    edges = canvas.canvas_json.get("edges", []) if canvas and canvas.canvas_json else []

    svg_content = _generate_canvas_svg(nodes, edges, project.title)
    return Response(content=svg_content, media_type="image/svg+xml")
