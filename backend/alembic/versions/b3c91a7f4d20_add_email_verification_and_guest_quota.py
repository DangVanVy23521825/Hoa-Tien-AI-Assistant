"""add email verification (OTP) and guest quota tracking

Revision ID: b3c91a7f4d20
Revises: f7dbe969141c
Create Date: 2026-08-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3c91a7f4d20'
down_revision: Union[str, Sequence[str], None] = 'f7dbe969141c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
    )
    # Tài khoản đã tồn tại trước tính năng này (admin + tài khoản test) được coi là
    # đã xác thực — nếu không, migration sẽ khoá chính mình ra khỏi production.
    op.execute("UPDATE users SET email_verified_at = now() WHERE email_verified_at IS NULL")

    op.add_column('chat_history', sa.Column('guest_id', sa.String(length=64), nullable=True))
    op.create_index('ix_chat_history_guest_id', 'chat_history', ['guest_id'])

    op.create_table(
        'email_otps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_otps_email', 'email_otps', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_email_otps_email', table_name='email_otps')
    op.drop_table('email_otps')
    op.drop_index('ix_chat_history_guest_id', table_name='chat_history')
    op.drop_column('chat_history', 'guest_id')
    op.drop_column('users', 'email_verified_at')
