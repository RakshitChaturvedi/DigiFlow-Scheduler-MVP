"""Migrate joblog_status_enum to lowercase

Revision ID: 40ff95104fbc
Revises: 3437a899ea4c
Create Date: 2025-06-26 22:00:56.833149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40ff95104fbc'
down_revision: Union[str, Sequence[str], None] = '3437a899ea4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

new_enum_values = ('pending', 'scheduled', 'in_progress', 'paused', 'completed', 'failed', 'cancelled')
old_enum_values = ('PENDING', 'SCHEDULED', 'IN_PROGRESS', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')

def upgrade():
    op.add_column("job_logs", sa.Column("status", sa.Enum("pending", "scheduled", "in_progress", "paused", "completed", "failed", "cancelled", name="joblog_status_enum"), nullable=False, server_default="pending"))

    op.execute("ALTER TYPE joblog_status_enum RENAME TO joblog_status_enum_old")
    
    # Create the new enum with all the correct values
    op.execute(f"CREATE TYPE joblog_status_enum AS ENUM{new_enum_values}")
    
    # Update the column type and migrate data
    op.execute("ALTER TABLE job_logs ALTER COLUMN status TYPE TEXT")
    for old, new in zip(old_enum_values, new_enum_values):
        op.execute(f"UPDATE job_logs SET status = '{new}' WHERE status = '{old.upper()}' OR status = '{old.lower()}'")
    op.execute("ALTER TABLE job_logs ALTER COLUMN status TYPE joblog_status_enum USING status::joblog_status_enum")
    
    op.execute("DROP TYPE joblog_status_enum_old")

def downgrade():
    op.drop_column("job_logs", "status")

    # Similar logic for downgrading, ensuring all values are handled
    op.execute("ALTER TYPE joblog_status_enum RENAME TO joblog_status_enum_new")
    
    op.execute(f"CREATE TYPE joblog_status_enum AS ENUM{old_enum_values}")

    op.execute("ALTER TABLE job_logs ALTER COLUMN status TYPE TEXT")
    for old, new in zip(old_enum_values, new_enum_values):
        op.execute(f"UPDATE job_logs SET status = '{old}' WHERE status = '{new}'")
    op.execute("ALTER TABLE job_logs ALTER COLUMN status TYPE joblog_status_enum USING status::joblog_status_enum")
    
    op.execute("DROP TYPE joblog_status_enum_new")

