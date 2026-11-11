"""Initial JEZTECH school and assessment schema.

Revision ID: 0001_initial
"""
from alembic import op
from app.main import Base
revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    # Baseline schema is defined once in SQLAlchemy metadata; Alembic records
    # the baseline revision so subsequent changes can be incremental migrations.
    Base.metadata.create_all(bind=op.get_bind(), tables=[Base.metadata.tables[name] for name in ("schools","users","classes","learners","subjects","exams","exam_papers","marks","audit_logs")])
def downgrade():
    # Destructive rollback is intentionally not automated for school records.
    raise RuntimeError("Initial schema downgrade is disabled to protect school data")
