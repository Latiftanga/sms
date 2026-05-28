"""Model realignment: category/designation enums, ssnit rename, promotion field cleanup

Revision ID: 007
Revises: 006
Create Date: 2025-05-27

Changes:
  - staff_member.ssnit  → ssnit_no
  - staff_promotion.date_obtained → date_promoted
  - staff_promotion.letter_reference dropped
"""

from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE staff_member RENAME COLUMN ssnit TO ssnit_no")
    op.execute("ALTER TABLE staff_promotion RENAME COLUMN date_obtained TO date_promoted")
    op.execute("ALTER TABLE staff_promotion DROP COLUMN IF EXISTS letter_reference")


def downgrade() -> None:
    op.execute("ALTER TABLE staff_member RENAME COLUMN ssnit_no TO ssnit")
    op.execute("ALTER TABLE staff_promotion RENAME COLUMN date_promoted TO date_obtained")
    op.execute("ALTER TABLE staff_promotion ADD COLUMN letter_reference VARCHAR(80)")
