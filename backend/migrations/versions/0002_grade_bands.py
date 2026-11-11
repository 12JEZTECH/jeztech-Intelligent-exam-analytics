"""Add configurable grade bands.
Revision ID: 0002_grade_bands
"""
from alembic import op
import sqlalchemy as sa
revision="0002_grade_bands"
down_revision="0001_initial"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table(
        "grade_bands",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("school_id",sa.Integer(),sa.ForeignKey("schools.id",ondelete="CASCADE"),nullable=False),
        sa.Column("curriculum",sa.String(length=20),nullable=False),
        sa.Column("label",sa.String(length=30),nullable=False),
        sa.Column("minimum_percent",sa.Float(),nullable=False),
        sa.Column("maximum_percent",sa.Float(),nullable=False),
        sa.Column("points",sa.Float(),nullable=True),
        sa.Column("descriptor",sa.String(length=120),nullable=True),
        sa.UniqueConstraint("school_id","curriculum","label",name="uq_grade_band_label")
    )
    op.create_index("ix_grade_bands_school_id","grade_bands",["school_id"])
def downgrade():
    op.drop_index("ix_grade_bands_school_id",table_name="grade_bands")
    op.drop_table("grade_bands")
