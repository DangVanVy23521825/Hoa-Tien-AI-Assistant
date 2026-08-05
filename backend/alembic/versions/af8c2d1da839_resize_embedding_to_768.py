"""resize embedding to 768 (switch self-host MiniLM -> Gemini embedding API)

Revision ID: af8c2d1da839
Revises: d5f2dd0ed353
Create Date: 2026-08-05 00:00:00.000000

Đổi provider embedding mặc định từ self-host (multilingual-MiniLM, 384 chiều —
liên tục OOM trên Railway Trial plan dù đã thử nhiều model nhẹ khác nhau) sang
API embedding của Gemini (768 chiều, tận dụng GEMINI_API_KEY sẵn có, không tự
host nên không có rủi ro RAM). Vector cũ (384 chiều) không tương thích kích
thước với model mới nên phải drop cột rồi tạo lại — dữ liệu embedding cũ mất,
cần chạy lại scripts/backfill_embeddings.py --force sau khi migrate.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'af8c2d1da839'
down_revision: Union[str, Sequence[str], None] = 'd5f2dd0ed353'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('procedures', 'embedding')
    op.drop_column('faq', 'embedding')
    op.drop_column('knowledge_articles', 'embedding')
    op.add_column('procedures', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('faq', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('knowledge_articles', sa.Column('embedding', Vector(768), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('knowledge_articles', 'embedding')
    op.drop_column('faq', 'embedding')
    op.drop_column('procedures', 'embedding')
    op.add_column('procedures', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('faq', sa.Column('embedding', Vector(384), nullable=True))
    op.add_column('knowledge_articles', sa.Column('embedding', Vector(384), nullable=True))
