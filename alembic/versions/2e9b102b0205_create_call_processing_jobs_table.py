"""create call processing jobs table

Revision ID: 2e9b102b0205
Revises: 2ce39126d89b
Create Date: 2026-11-01 12:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e9b102b0205'
down_revision: Union[str, Sequence[str], None] = '2ce39126d89b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'call_processing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_call_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), server_default='call_intelligence', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
        sa.Column('claim_token', sa.String(length=36), nullable=True),
        sa.Column('locked_by', sa.String(length=100), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_call_id'], ['agent_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_call_id', name='uq_call_processing_jobs_agent_call_id'),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'dead_letter')",
            name='ck_call_processing_jobs_status'
        ),
        sa.CheckConstraint('attempts >= 0', name='ck_call_processing_jobs_attempts'),
        sa.CheckConstraint('max_attempts > 0', name='ck_call_processing_jobs_max_attempts'),
        sa.CheckConstraint(
            "(status = 'processing' AND claim_token IS NOT NULL AND lease_expires_at IS NOT NULL) OR (status != 'processing')",
            name='ck_call_processing_jobs_processing_state'
        )
    )
    op.create_index(op.f('ix_call_processing_jobs_status'), 'call_processing_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_call_processing_jobs_claim_token'), 'call_processing_jobs', ['claim_token'], unique=False)
    op.create_index(op.f('ix_call_processing_jobs_lease_expires_at'), 'call_processing_jobs', ['lease_expires_at'], unique=False)
    op.create_index(op.f('ix_call_processing_jobs_next_run_at'), 'call_processing_jobs', ['next_run_at'], unique=False)
    op.create_index('ix_call_processing_jobs_claim', 'call_processing_jobs', ['status', 'next_run_at', 'lease_expires_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_call_processing_jobs_claim', table_name='call_processing_jobs')
    op.drop_index(op.f('ix_call_processing_jobs_next_run_at'), table_name='call_processing_jobs')
    op.drop_index(op.f('ix_call_processing_jobs_lease_expires_at'), table_name='call_processing_jobs')
    op.drop_index(op.f('ix_call_processing_jobs_claim_token'), table_name='call_processing_jobs')
    op.drop_index(op.f('ix_call_processing_jobs_status'), table_name='call_processing_jobs')
    op.drop_table('call_processing_jobs')
