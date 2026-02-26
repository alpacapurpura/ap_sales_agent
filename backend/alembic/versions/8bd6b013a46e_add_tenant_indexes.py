"""db_tech_debt_cleanup

Revision ID: 8bd6b013a46e
Revises: f43d58dc53c2
Create Date: 2026-02-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '8bd6b013a46e'
down_revision: Union[str, None] = 'f43d58dc53c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- TASK 1: ADD MISSING INDEXES CONCURRENTLY ---
    # Updated list based on current codebase and schema
    # users removed (tenant_id dropped in f43d58dc53c2)
    # user_tenants added (needs reverse index for tenant_id lookup)
    tables_with_tenant_id = [
        'leads',
        'messages',
        'agent_traces',
        'llm_call_logs',
        'appointments',
        'journey_progress',
        'booking_links',
        'marketing_assets',
        'objections',
        'offer_logs',
        'products',
        'prompt_versions',
        'sensitive_data',
        'avatar_definitions',
        'user_tenants'
    ]

    # We use autocommit block for concurrent operations
    with op.get_context().autocommit_block():
        conn = op.get_bind()
        inspector = Inspector.from_engine(conn)
        existing_tables = inspector.get_table_names()

        # 1. Add tenant_id indexes
        for table in tables_with_tenant_id:
            if table not in existing_tables:
                print(f"Skipping index for non-existent table: {table}")
                continue
                
            index_name = f'ix_{table}_tenant_id'
            # Postgres supports IF NOT EXISTS for indexes
            op.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table} (tenant_id)"
            )
        
        # --- TASK 2: REMOVE REDUNDANT INDEXES CONCURRENTLY ---
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_users_clerk_id")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_tenants_slug")

        # --- TASK 3: ADD INDEXES TO MARKETING TABLES ---
        marketing_tables = ['customer_profiles', 'customer_identities', 'journey_events']
        for table in marketing_tables:
             if table not in existing_tables:
                print(f"Skipping index for non-existent table: {table}")
                continue
                
             # Check if column tenant_id exists in table
             columns = [c['name'] for c in inspector.get_columns(table)]
             if 'tenant_id' not in columns:
                 print(f"Skipping index for table {table} as tenant_id column missing")
                 continue

             index_name = f'ix_{table}_tenant_id'
             op.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table} (tenant_id)"
            )


def downgrade() -> None:
    tables_with_tenant_id = [
        'leads',
        'messages',
        'agent_traces',
        'llm_call_logs',
        'appointments',
        'journey_progress',
        'booking_links',
        'marketing_assets',
        'objections',
        'offer_logs',
        'products',
        'prompt_versions',
        'sensitive_data',
        'avatar_definitions',
        'user_tenants',
        'customer_profiles',
        'customer_identities',
        'journey_events'
    ]
    
    with op.get_context().autocommit_block():
        for table in tables_with_tenant_id:
            index_name = f'ix_{table}_tenant_id'
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")
        
        # Re-create redundant indexes (if needed for rollback)
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_clerk_id ON users (clerk_id)")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tenants_slug ON tenants (slug)")
