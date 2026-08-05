"""resize embedding to 384 (switch bge-m3 -> multilingual-MiniLM self-host)

Revision ID: d5f2dd0ed353
Revises: 82f5e29f7a0c
Create Date: 2026-08-05 00:00:00.000000

Đổi provider embedding mặc định từ bge-m3 (1024 chiều, self-host gây OOM trên
Railway Trial plan kể cả bản quantize) sang paraphrase-multilingual-MiniLM-L12-v2
(384 chiều, self-host nhẹ hơn nhiều, ~700MB RAM). Vector cũ (1024 chiều) không
tương thích kích thước với model mới nên phải drop cột rồi tạo lại — dữ liệu
embedding cũ mất, cần chạy lại scripts/backfill_embeddings.py --force sau khi
migrate.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'd5f2dd0ed353'
down_revision: Union[str, Sequence[str], None] = '82f5e29f7a0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('procedures', 'embedding')
    op.drop_column('faq', 'embedding')
    op.drop_column('knowledge_articles', 'embedding')
    op.add_column('procedures', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('faq', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('knowledge_articles', sa.Column('embedding', Vector(384), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('knowledge_articles', 'embedding')
    op.drop_column('faq', 'embedding')
    op.drop_column('procedures', 'embedding')
    op.add_column('procedures', sa.Column('embedding', Vector(1024), nullable=True))
    op.add_column('faq', sa.Column('embedding', Vector(1024), nullable=True))
    op.add_column('knowledge_articles', sa.Column('embedding', Vector(1024), nullable=True))
