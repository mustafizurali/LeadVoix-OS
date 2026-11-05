"""add crm automation and normalization schema

Revision ID: 3c8d1e2f4a5b
Revises: 2e9b102b0205
Create Date: 2026-11-01 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.app.utils.phone import normalize_phone


# revision identifiers, used by Alembic.
revision: str = '3c8d1e2f4a5b'
down_revision: Union[str, Sequence[str], None] = '2e9b102b0205'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Step 1: Add new nullable columns to existing tables
    # =========================================================================

    # 1.1 leads
    op.add_column('leads', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_leads_owner_id_users', 'leads', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_leads_owner_id', 'leads', ['owner_id'])

    op.add_column('leads', sa.Column('company_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_leads_company_id_companies', 'leads', 'companies', ['company_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_leads_company_id', 'leads', ['company_id'])

    op.add_column('leads', sa.Column('phone_normalized', sa.String(length=32), nullable=True))
    op.add_column('leads', sa.Column('phone_extension', sa.String(length=10), nullable=True))

    # 1.2 contacts
    op.add_column('contacts', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_contacts_owner_id_users', 'contacts', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_contacts_owner_id', 'contacts', ['owner_id'])

    op.add_column('contacts', sa.Column('company_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_contacts_company_id_companies', 'contacts', 'companies', ['company_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_contacts_company_id', 'contacts', ['company_id'])

    op.add_column('contacts', sa.Column('lead_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_contacts_lead_id_leads', 'contacts', 'leads', ['lead_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_contacts_lead_id', 'contacts', ['lead_id'])

    op.add_column('contacts', sa.Column('phone_normalized', sa.String(length=32), nullable=True))
    op.add_column('contacts', sa.Column('phone_extension', sa.String(length=10), nullable=True))

    # 1.3 agent_calls
    op.add_column('agent_calls', sa.Column('caller_phone_normalized', sa.String(length=32), nullable=True))
    op.add_column('agent_calls', sa.Column('caller_phone_extension', sa.String(length=10), nullable=True))

    # 1.4 tasks
    op.add_column('tasks', sa.Column('agent_call_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tasks_agent_call_id_agent_calls', 'tasks', 'agent_calls', ['agent_call_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_tasks_agent_call_id', 'tasks', ['agent_call_id'])

    # 1.5 follow_up_tasks (organization_id nullable; no FK on agent_call_id while orphans remain)
    op.add_column('follow_up_tasks', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_follow_up_tasks_org_id_orgs', 'follow_up_tasks', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_follow_up_tasks_organization_id', 'follow_up_tasks', ['organization_id'])

    # =========================================================================
    # Step 2: Create new CRM tables
    # =========================================================================

    # 2.1 deal_stage_history
    op.create_table(
        'deal_stage_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('from_stage_id', sa.Integer(), nullable=True),
        sa.Column('to_stage_id', sa.Integer(), nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('exited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('changed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('entry_type', sa.String(length=30), server_default='transition', nullable=False),
        sa.Column('is_verified_transition', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_stage_id'], ['pipeline_stages.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deal_stage_history_id', 'deal_stage_history', ['id'])
    op.create_index('ix_deal_stage_history_deal_active', 'deal_stage_history', ['deal_id', 'exited_at'])
    op.create_index('ix_deal_stage_history_org_deal', 'deal_stage_history', ['organization_id', 'deal_id', 'entered_at'])

    # 2.2 activities (operational activity timeline)
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('agent_call_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_call_id'], ['agent_calls.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_activities_id', 'activities', ['id'])
    op.create_index('ix_activities_org_created', 'activities', ['organization_id', 'created_at'])
    op.create_index('ix_activities_org_lead', 'activities', ['organization_id', 'lead_id', 'created_at'])
    op.create_index('ix_activities_org_contact', 'activities', ['organization_id', 'contact_id', 'created_at'])
    op.create_index('ix_activities_org_deal', 'activities', ['organization_id', 'deal_id', 'created_at'])
    op.create_index('ix_activities_org_call', 'activities', ['organization_id', 'agent_call_id'])

    # =========================================================================
    # Step 3: Compound Indexes
    # =========================================================================
    op.create_index('ix_leads_org_phone_norm', 'leads', ['organization_id', 'phone_normalized'])
    op.create_index('ix_contacts_org_phone_norm', 'contacts', ['organization_id', 'phone_normalized'])
    op.create_index('ix_agent_calls_org_phone_norm', 'agent_calls', ['organization_id', 'caller_phone_normalized'])
    op.create_index('ix_follow_up_tasks_org_call', 'follow_up_tasks', ['organization_id', 'agent_call_id'])

    # =========================================================================
    # Step 4: Non-Destructive Data Backfill
    # =========================================================================
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # 4.1 Backfill follow_up_tasks.organization_id from agent_calls
        # Only updates tasks where agent_call exists. Orphans remain organization_id=NULL.
        session.execute(sa.text("""
            UPDATE follow_up_tasks
            SET organization_id = agent_calls.organization_id
            FROM agent_calls
            WHERE follow_up_tasks.agent_call_id = agent_calls.id
              AND follow_up_tasks.organization_id IS NULL;
        """))

        # 4.2 Backfill company_id strictly when match_count == 1
        # For leads:
        session.execute(sa.text("""
            UPDATE leads l
            SET company_id = matched.company_id
            FROM (
                SELECT l_sub.id AS lead_id, MIN(c.id) AS company_id
                FROM leads l_sub
                JOIN companies c
                  ON c.organization_id = l_sub.organization_id
                 AND LOWER(TRIM(c.name)) = LOWER(TRIM(l_sub.company))
                WHERE l_sub.company IS NOT NULL
                  AND TRIM(l_sub.company) != ''
                  AND l_sub.company_id IS NULL
                GROUP BY l_sub.id
                HAVING COUNT(c.id) = 1
            ) matched
            WHERE l.id = matched.lead_id;
        """))

        # For contacts:
        session.execute(sa.text("""
            UPDATE contacts ct
            SET company_id = matched.company_id
            FROM (
                SELECT ct_sub.id AS contact_id, MIN(c.id) AS company_id
                FROM contacts ct_sub
                JOIN companies c
                  ON c.organization_id = ct_sub.organization_id
                 AND LOWER(TRIM(c.name)) = LOWER(TRIM(ct_sub.company))
                WHERE ct_sub.company IS NOT NULL
                  AND TRIM(ct_sub.company) != ''
                  AND ct_sub.company_id IS NULL
                GROUP BY ct_sub.id
                HAVING COUNT(c.id) = 1
            ) matched
            WHERE ct.id = matched.contact_id;
        """))

        # 4.3 Backfill phone_normalized & phone_extension for leads, contacts, agent_calls
        # Fetches rows and applies standardized normalization policy
        raw_leads = session.execute(sa.text("SELECT id, phone FROM leads WHERE phone IS NOT NULL;")).fetchall()
        for row in raw_leads:
            norm_val, ext_val = normalize_phone(row[1])
            if norm_val or ext_val:
                session.execute(
                    sa.text("UPDATE leads SET phone_normalized = :p, phone_extension = :ext WHERE id = :id"),
                    {"p": norm_val, "ext": ext_val, "id": row[0]}
                )

        raw_contacts = session.execute(sa.text("SELECT id, phone FROM contacts WHERE phone IS NOT NULL;")).fetchall()
        for row in raw_contacts:
            norm_val, ext_val = normalize_phone(row[1])
            if norm_val or ext_val:
                session.execute(
                    sa.text("UPDATE contacts SET phone_normalized = :p, phone_extension = :ext WHERE id = :id"),
                    {"p": norm_val, "ext": ext_val, "id": row[0]}
                )

        raw_calls = session.execute(sa.text("SELECT id, caller_phone FROM agent_calls WHERE caller_phone IS NOT NULL;")).fetchall()
        for row in raw_calls:
            norm_val, ext_val = normalize_phone(row[1])
            if norm_val or ext_val:
                session.execute(
                    sa.text("UPDATE agent_calls SET caller_phone_normalized = :p, caller_phone_extension = :ext WHERE id = :id"),
                    {"p": norm_val, "ext": ext_val, "id": row[0]}
                )

        # 4.4 Backfill initial legacy deal stage history (Honest Backfill: is_verified_transition = False)
        session.execute(sa.text("""
            INSERT INTO deal_stage_history (
                organization_id,
                deal_id,
                from_stage_id,
                to_stage_id,
                entered_at,
                exited_at,
                duration_seconds,
                changed_by_user_id,
                entry_type,
                is_verified_transition,
                created_at
            )
            SELECT
                d.organization_id,
                d.id,
                NULL,
                d.stage_id,
                COALESCE(d.updated_at, d.created_at),
                NULL,
                NULL,
                d.owner_id,
                'legacy_snapshot',
                FALSE,
                COALESCE(d.created_at, NOW())
            FROM deals d
            WHERE d.stage_id IS NOT NULL;
        """))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    # Drop compound indexes
    op.drop_index('ix_follow_up_tasks_org_call', table_name='follow_up_tasks')
    op.drop_index('ix_agent_calls_org_phone_norm', table_name='agent_calls')
    op.drop_index('ix_contacts_org_phone_norm', table_name='contacts')
    op.drop_index('ix_leads_org_phone_norm', table_name='leads')

    # Drop tables
    op.drop_table('activities')
    op.drop_table('deal_stage_history')

    # Drop added columns from follow_up_tasks
    op.drop_index('ix_follow_up_tasks_organization_id', table_name='follow_up_tasks')
    op.drop_constraint('fk_follow_up_tasks_org_id_orgs', 'follow_up_tasks', type_='foreignkey')
    op.drop_column('follow_up_tasks', 'organization_id')

    # Drop added columns from tasks
    op.drop_index('ix_tasks_agent_call_id', table_name='tasks')
    op.drop_constraint('fk_tasks_agent_call_id_agent_calls', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'agent_call_id')

    # Drop added columns from agent_calls
    op.drop_column('agent_calls', 'caller_phone_extension')
    op.drop_column('agent_calls', 'caller_phone_normalized')

    # Drop added columns from contacts
    op.drop_column('contacts', 'phone_extension')
    op.drop_column('contacts', 'phone_normalized')
    op.drop_index('ix_contacts_lead_id', table_name='contacts')
    op.drop_constraint('fk_contacts_lead_id_leads', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'lead_id')
    op.drop_index('ix_contacts_company_id', table_name='contacts')
    op.drop_constraint('fk_contacts_company_id_companies', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'company_id')
    op.drop_index('ix_contacts_owner_id', table_name='contacts')
    op.drop_constraint('fk_contacts_owner_id_users', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'owner_id')

    # Drop added columns from leads
    op.drop_column('leads', 'phone_extension')
    op.drop_column('leads', 'phone_normalized')
    op.drop_index('ix_leads_company_id', table_name='leads')
    op.drop_constraint('fk_leads_company_id_companies', 'leads', type_='foreignkey')
    op.drop_column('leads', 'company_id')
    op.drop_index('ix_leads_owner_id', table_name='leads')
    op.drop_constraint('fk_leads_owner_id_users', 'leads', type_='foreignkey')
    op.drop_column('leads', 'owner_id')
