"""add knowledge_articles

Revision ID: 58e25152c7b5
Revises: 60022f91b341
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '58e25152c7b5'
down_revision: Union[str, Sequence[str], None] = '60022f91b341'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('knowledge_articles',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('keywords', sa.JSON(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('source_citation', sa.String(length=500), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('knowledge_articles')
