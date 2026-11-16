"""Add validation and graph models

Revision ID: 4d81ec57b8a5
Revises: 3c39ec46a7a4
Create Date: 2026-11-16 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d81ec57b8a5'
down_revision: Union[str, None] = '3c39ec46a7a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if is_postgres:
        # Add 'validation' to existing agent_type enum
        try:
            op.execute("ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'validation'")
        except Exception:
            pass

        requirement_category = sa.Enum('functional', 'non_functional', 'constraint', name='requirement_category')
        verification_status = sa.Enum('verified', 'unverified', 'contradicted', name='verification_status')
        issue_severity = sa.Enum('critical', 'warning', 'review', name='issue_severity')
    else:
        requirement_category = sa.String(50)
        verification_status = sa.String(50)
        issue_severity = sa.String(50)

    # 1. requirements
    if 'requirements' not in existing_tables:
        op.create_table(
            'requirements',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('category', requirement_category, nullable=False),
            sa.Column('priority', sa.String(length=50), server_default='high', nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_requirements_project_id'), 'requirements', ['project_id'], unique=False)

    # 2. features
    if 'features' not in existing_tables:
        op.create_table(
            'features',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('user_story', sa.Text(), nullable=True),
            sa.Column('is_mvp', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_features_project_id'), 'features', ['project_id'], unique=False)

    # 3. feature_requirement_mappings
    if 'feature_requirement_mappings' not in existing_tables:
        op.create_table(
            'feature_requirement_mappings',
            sa.Column('feature_id', sa.UUID(), nullable=False),
            sa.Column('requirement_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['feature_id'], ['features.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['requirement_id'], ['requirements.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('feature_id', 'requirement_id')
        )

    # 4. architecture_components
    if 'architecture_components' not in existing_tables:
        op.create_table(
            'architecture_components',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('component_id_name', sa.String(length=100), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('component_type', sa.String(length=100), nullable=False),
            sa.Column('tech_stack', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_architecture_components_project_id'), 'architecture_components', ['project_id'], unique=False)

    # 5. component_feature_mappings
    if 'component_feature_mappings' not in existing_tables:
        op.create_table(
            'component_feature_mappings',
            sa.Column('component_id', sa.UUID(), nullable=False),
            sa.Column('feature_id', sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(['component_id'], ['architecture_components.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['feature_id'], ['features.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('component_id', 'feature_id')
        )

    # 6. decisions
    if 'decisions' not in existing_tables:
        op.create_table(
            'decisions',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('topic', sa.String(length=255), nullable=False),
            sa.Column('chosen_option', sa.String(length=255), nullable=False),
            sa.Column('why_chosen', sa.Text(), nullable=False),
            sa.Column('why_not_alternatives', sa.Text(), nullable=True),
            sa.Column('trade_offs', sa.Text(), nullable=True),
            sa.Column('assumptions', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_decisions_project_id'), 'decisions', ['project_id'], unique=False)

    # 7. evidence_claims
    if 'evidence_claims' not in existing_tables:
        op.create_table(
            'evidence_claims',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('decision_id', sa.UUID(), nullable=True),
            sa.Column('claim_text', sa.Text(), nullable=False),
            sa.Column('source_name', sa.String(length=255), nullable=True),
            sa.Column('source_url', sa.String(length=500), nullable=True),
            sa.Column('status', verification_status, nullable=False),
            sa.Column('checked_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_evidence_claims_project_id'), 'evidence_claims', ['project_id'], unique=False)

    # 8. validation_issues
    if 'validation_issues' not in existing_tables:
        op.create_table(
            'validation_issues',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('severity', issue_severity, nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('suggested_fix', sa.Text(), nullable=True),
            sa.Column('affected_entities', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_validation_issues_project_id'), 'validation_issues', ['project_id'], unique=False)

    # 9. document_chunks
    if 'document_chunks' not in existing_tables:
        op.create_table(
            'document_chunks',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_id', sa.UUID(), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('metadata_json', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_document_chunks_project_id'), 'document_chunks', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_table('document_chunks')
    op.drop_table('validation_issues')
    op.drop_table('evidence_claims')
    op.drop_table('decisions')
    op.drop_table('component_feature_mappings')
    op.drop_table('architecture_components')
    op.drop_table('feature_requirement_mappings')
    op.drop_table('features')
    op.drop_table('requirements')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        sa.Enum(name='issue_severity').drop(bind, checkfirst=False)
        sa.Enum(name='verification_status').drop(bind, checkfirst=False)
        sa.Enum(name='requirement_category').drop(bind, checkfirst=False)
