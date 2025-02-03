"""初始数据库迁移。

Revision ID: 001_initial
Revises: 
Create Date: 2024-03-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建平台表
    op.create_table(
        'platform',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('base_url', sa.String(length=200), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 创建标签表
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['parent_id'], ['tag.id'], ondelete='SET NULL')
    )

    # 创建内容表
    op.create_table(
        'content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('publish_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='draft'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('media', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.ForeignKeyConstraint(['platform_id'], ['platform.id'], ondelete='CASCADE')
    )

    # 创建内容标签关联表
    op.create_table(
        'content_tag',
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, default=1.0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('content_id', 'tag_id'),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE')
    )

    # 创建评论表
    op.create_table(
        'comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('publish_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='published'),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comment.id'], ondelete='CASCADE')
    )

    # 创建索引
    op.create_index('ix_platform_name', 'platform', ['name'])
    op.create_index('ix_tag_name', 'tag', ['name'])
    op.create_index('ix_content_platform_id', 'content', ['platform_id'])
    op.create_index('ix_content_publish_time', 'content', ['publish_time'])
    op.create_index('ix_content_status', 'content', ['status'])
    op.create_index('ix_comment_content_id', 'comment', ['content_id'])
    op.create_index('ix_comment_parent_id', 'comment', ['parent_id'])
    op.create_index('ix_comment_publish_time', 'comment', ['publish_time'])
    op.create_index('ix_comment_status', 'comment', ['status'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_comment_status', 'comment')
    op.drop_index('ix_comment_publish_time', 'comment')
    op.drop_index('ix_comment_parent_id', 'comment')
    op.drop_index('ix_comment_content_id', 'comment')
    op.drop_index('ix_content_status', 'content')
    op.drop_index('ix_content_publish_time', 'content')
    op.drop_index('ix_content_platform_id', 'content')
    op.drop_index('ix_tag_name', 'tag')
    op.drop_index('ix_platform_name', 'platform')

    # 删除表
    op.drop_table('comment')
    op.drop_table('content_tag')
    op.drop_table('content')
    op.drop_table('tag')
    op.drop_table('platform') 