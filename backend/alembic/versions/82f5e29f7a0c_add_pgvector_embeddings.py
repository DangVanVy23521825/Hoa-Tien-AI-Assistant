"""add pgvector embeddings

Revision ID: 82f5e29f7a0c
Revises: 58e25152c7b5
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '82f5e29f7a0c'
down_revision: Union[str, Sequence[str], None] = '58e25152c7b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column('procedures', sa.Column('embedding', Vector(1024), nullable=True))
    op.add_column('faq', sa.Column('embedding', Vector(1024), nullable=True))
    op.add_column('knowledge_articles', sa.Column('embedding', Vector(1024), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('knowledge_articles', 'embedding')
    op.drop_column('faq', 'embedding')
    op.drop_column('procedures', 'embedding')
    op.execute("DROP EXTENSION IF EXISTS vector")
