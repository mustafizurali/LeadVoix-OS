"""create jarvis schema and operational tables

Revision ID: 4f7e2a1b9c3d
Revises: 3c8d1e2f4a5b
Create Date: 2026-11-11 13:00:00.000000

Phase B — Isolated JARVIS Operational Data Boundary
Implements:
- Schema: jarvis
- jarvis.jarvis_tasks
- jarvis.dispatch_idempotency
- jarvis.task_attempts
- jarvis.approval_records
- jarvis.audit_logs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f7e2a1b9c3d'
down_revision: Union[str, Sequence[str], None] = '3c8d1e2f4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure isolated jarvis schema exists
    # In hardened least-privilege environments, schema 'jarvis' is pre-bootstrapped
    # and owned by 'leadvoix_migrator' by the privileged staging/production setup SQL.
    # We check if it exists before executing CREATE SCHEMA to avoid requiring database-level
    # CREATE privilege for the migration user.
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_schema("jarvis"):
        raise RuntimeError(
            "Required 'jarvis' schema is missing. "
            "Run the privileged schema bootstrap before migration."
        )

    # 2. jarvis.jarvis_tasks
    op.create_table(
        'jarvis_tasks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=150), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
        sa.Column('organization_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('claim_token', sa.String(length=36), nullable=True),
        sa.Column('locked_by', sa.String(length=100), nullable=True),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_jarvis_tasks_idempotency_key'),
        schema='jarvis'
    )
    op.create_index('ix_jarvis_tasks_claim', 'jarvis_tasks', ['status', 'next_run_at', 'lease_expires_at'], schema='jarvis')
    op.create_index('ix_jarvis_tasks_status', 'jarvis_tasks', ['status'], schema='jarvis')
    op.create_index('ix_jarvis_tasks_task_type', 'jarvis_tasks', ['task_type'], schema='jarvis')
    op.create_index('ix_jarvis_tasks_idempotency_key', 'jarvis_tasks', ['idempotency_key'], schema='jarvis')
    op.create_index('ix_jarvis_tasks_organization_id', 'jarvis_tasks', ['organization_id'], schema='jarvis')
    op.create_index('ix_jarvis_tasks_claim_token', 'jarvis_tasks', ['claim_token'], schema='jarvis')

    # 3. jarvis.dispatch_idempotency
    op.create_table(
        'dispatch_idempotency',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('digest_type', sa.String(length=50), nullable=False),
        sa.Column('window_date', sa.Date(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=150), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='in_flight', nullable=False),
        sa.Column('claim_token', sa.String(length=36), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('telegram_message_id', sa.BigInteger(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.JSON(), nullable=True),
        sa.Column('cooldown_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_jarvis_dispatch_idempotency_key'),
        schema='jarvis'
    )
    op.create_index('ix_jarvis_dispatch_lookup', 'dispatch_idempotency', ['organization_id', 'digest_type', 'window_date'], schema='jarvis')
    op.create_index('ix_jarvis_dispatch_idempotency_key', 'dispatch_idempotency', ['idempotency_key'], schema='jarvis')
    op.create_index('ix_jarvis_dispatch_status', 'dispatch_idempotency', ['status'], schema='jarvis')

    # 4. jarvis.task_attempts
    op.create_table(
        'task_attempts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('worker_instance', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['jarvis.jarvis_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='jarvis'
    )
    op.create_index('ix_jarvis_task_attempts_task_id', 'task_attempts', ['task_id'], schema='jarvis')

    # 5. jarvis.approval_records
    op.create_table(
        'approval_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=True),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('risk_tier', sa.String(length=20), server_default='high', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='pending', nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('payload_preview', sa.JSON(), nullable=False),
        sa.Column('requested_by', sa.String(length=100), server_default='jarvis_autonomous_engine', nullable=False),
        sa.Column('responded_by', sa.String(length=100), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_jarvis_approval_token_hash'),
        schema='jarvis'
    )
    op.create_index('ix_jarvis_approval_status', 'approval_records', ['status', 'expires_at'], schema='jarvis')
    op.create_index('ix_jarvis_approval_action_type', 'approval_records', ['action_type'], schema='jarvis')

    # 6. jarvis.audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), server_default='jarvis_worker', nullable=False),
        sa.Column('organization_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='jarvis'
    )
    op.create_index('ix_jarvis_audit_created_at', 'audit_logs', ['created_at'], schema='jarvis')
    op.create_index('ix_jarvis_audit_event_type', 'audit_logs', ['event_type'], schema='jarvis')

    # 7. Post-table-creation least-privilege hardening for PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("""
            DO $$
            BEGIN
                -- Explicit operational grants for mutable tables
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'jarvis_operator') THEN
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.jarvis_tasks TO jarvis_operator;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.dispatch_idempotency TO jarvis_operator;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.task_attempts TO jarvis_operator;
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE jarvis.approval_records TO jarvis_operator;

                    -- Audit Log Immutability: Strictly append-only (SELECT & INSERT). Block UPDATE, DELETE, TRUNCATE
                    GRANT SELECT, INSERT ON TABLE jarvis.audit_logs TO jarvis_operator;
                    REVOKE UPDATE, DELETE, TRUNCATE ON TABLE jarvis.audit_logs FROM jarvis_operator;

                    -- Sequences:
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA jarvis TO jarvis_operator;
                END IF;

                -- Read-only role access
                IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'jarvis_business_reader') THEN
                    GRANT SELECT ON ALL TABLES IN SCHEMA jarvis TO jarvis_business_reader;
                END IF;
            END $$;
        """)

        # 8. Append-only protection trigger on jarvis.audit_logs
        op.execute("""
            CREATE OR REPLACE FUNCTION jarvis.prevent_audit_log_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'Security Violation: jarvis.audit_logs is an append-only audit trail. % operations are strictly forbidden.', TG_OP;
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_protect_audit_logs_mutation ON jarvis.audit_logs;
            CREATE TRIGGER trg_protect_audit_logs_mutation
            BEFORE UPDATE OR DELETE ON jarvis.audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION jarvis.prevent_audit_log_mutation();

            DROP TRIGGER IF EXISTS trg_protect_audit_logs_truncate ON jarvis.audit_logs;
            CREATE TRIGGER trg_protect_audit_logs_truncate
            BEFORE TRUNCATE ON jarvis.audit_logs
            FOR EACH STATEMENT
            EXECUTE FUNCTION jarvis.prevent_audit_log_mutation();
        """)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_protect_audit_logs_mutation ON jarvis.audit_logs;")
        op.execute("DROP TRIGGER IF EXISTS trg_protect_audit_logs_truncate ON jarvis.audit_logs;")
        op.execute("DROP FUNCTION IF EXISTS jarvis.prevent_audit_log_mutation() CASCADE;")

    op.drop_table('audit_logs', schema='jarvis')
    op.drop_table('approval_records', schema='jarvis')
    op.drop_table('task_attempts', schema='jarvis')
    op.drop_table('dispatch_idempotency', schema='jarvis')
    op.drop_table('jarvis_tasks', schema='jarvis')
    op.execute("DROP SCHEMA IF EXISTS jarvis CASCADE;")
