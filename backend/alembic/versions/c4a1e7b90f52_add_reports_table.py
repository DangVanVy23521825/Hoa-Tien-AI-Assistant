"""add reports table for citizen feedback

Revision ID: c4a1e7b90f52
Revises: b3c91a7f4d20
Create Date: 2026-08-13

Bảng mới hoàn toàn, không đụng bảng cũ — chạy trên production không ảnh hưởng
dữ liệu đang có.

`seq` dùng IDENTITY thay vì SERIAL/autoincrement: đây không phải khoá chính nên
`autoincrement=True` của SQLAlchemy sẽ bị bỏ qua và cột ra INTEGER trần.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4a1e7b90f52'
down_revision: Union[str, Sequence[str], None] = 'b3c91a7f4d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seq', sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('seq'),
    )
    op.create_index('ix_reports_user_id', 'reports', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_reports_user_id', table_name='reports')
    op.drop_table('reports')
