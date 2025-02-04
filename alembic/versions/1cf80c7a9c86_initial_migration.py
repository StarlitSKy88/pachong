"""Initial migration

Revision ID: 1cf80c7a9c86
Revises: 001_initial
Create Date: 2025-02-04 09:36:58.307807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '1cf80c7a9c86'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('platforms',
    sa.Column('name', sa.String(length=50), nullable=False, comment='平台名称'),
    sa.Column('description', sa.String(length=200), nullable=True, comment='平台描述'),
    sa.Column('base_url', sa.String(length=200), nullable=False, comment='平台基础URL'),
    sa.Column('enabled', sa.Boolean(), nullable=False, comment='是否启用'),
    sa.Column('config', sa.JSON(), nullable=True, comment='平台配置'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('reports',
    sa.Column('title', sa.String(length=200), nullable=False, comment='标题'),
    sa.Column('summary', sa.Text(), nullable=False, comment='摘要'),
    sa.Column('report_type', sa.String(length=50), nullable=False, comment='报告类型'),
    sa.Column('report_date', sa.DateTime(), nullable=False, comment='报告日期'),
    sa.Column('create_time', sa.DateTime(), nullable=True),
    sa.Column('update_time', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tags',
    sa.Column('name', sa.String(length=50), nullable=False, comment='标签名称'),
    sa.Column('description', sa.String(length=200), nullable=True, comment='标签描述'),
    sa.Column('parent_id', sa.Integer(), nullable=True, comment='父标签ID'),
    sa.Column('level', sa.Integer(), nullable=False, comment='标签层级'),
    sa.Column('weight', sa.Float(), nullable=False, comment='标签权重'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.ForeignKeyConstraint(['parent_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('contents',
    sa.Column('title', sa.String(length=200), nullable=False, comment='标题'),
    sa.Column('content', sa.Text(), nullable=False, comment='内容'),
    sa.Column('author_name', sa.String(length=100), nullable=False, comment='作者名称'),
    sa.Column('author_id', sa.String(length=100), nullable=False, comment='作者ID'),
    sa.Column('platform_id', sa.Integer(), nullable=False, comment='平台ID'),
    sa.Column('url', sa.String(length=500), nullable=False, comment='原始链接'),
    sa.Column('images', sa.JSON(), nullable=False, comment='图片列表'),
    sa.Column('video', sa.String(length=500), nullable=True, comment='视频链接'),
    sa.Column('publish_time', sa.DateTime(), nullable=False, comment='发布时间'),
    sa.Column('content_type', sa.Enum('ARTICLE', 'VIDEO', 'IMAGE', 'AUDIO', name='contenttype'), nullable=False, comment='内容类型'),
    sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', 'DELETED', name='contentstatus'), nullable=False, comment='内容状态'),
    sa.Column('cover_image', sa.String(length=500), nullable=True, comment='封面图片'),
    sa.Column('summary', sa.String(length=500), nullable=True, comment='摘要'),
    sa.Column('word_count', sa.Integer(), nullable=False, comment='字数'),
    sa.Column('read_time', sa.Integer(), nullable=False, comment='阅读时间(秒)'),
    sa.Column('is_original', sa.Boolean(), nullable=False, comment='是否原创'),
    sa.Column('is_premium', sa.Boolean(), nullable=False, comment='是否优质内容'),
    sa.Column('is_sensitive', sa.Boolean(), nullable=False, comment='是否敏感内容'),
    sa.Column('meta_info', sa.JSON(), nullable=True, comment='元数据'),
    sa.Column('stats', sa.JSON(), nullable=True, comment='统计数据'),
    sa.Column('score', sa.Float(), nullable=False, comment='内容评分'),
    sa.Column('quality_check', sa.JSON(), nullable=True, comment='质量检查结果'),
    sa.Column('keywords', sa.JSON(), nullable=True, comment='关键词'),
    sa.Column('categories', sa.JSON(), nullable=True, comment='分类'),
    sa.Column('language', sa.String(length=10), nullable=True, comment='语言'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('comments',
    sa.Column('content_id', sa.Integer(), nullable=False, comment='内容ID'),
    sa.Column('parent_id', sa.Integer(), nullable=True, comment='父评论ID'),
    sa.Column('user_id', sa.String(length=100), nullable=False, comment='用户ID'),
    sa.Column('username', sa.String(length=100), nullable=True, comment='用户名'),
    sa.Column('likes', sa.Integer(), nullable=False, comment='点赞数'),
    sa.Column('replies', sa.Integer(), nullable=False, comment='回复数'),
    sa.Column('is_top', sa.Boolean(), nullable=False, comment='是否置顶'),
    sa.Column('status', sa.String(length=20), nullable=False, comment='状态'),
    sa.Column('meta_info', sa.JSON(), nullable=True, comment='元数据'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('content_tags',
    sa.Column('content_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('content_id', 'tag_id')
    )
    op.create_table('generated_contents',
    sa.Column('title', sa.String(length=200), nullable=False, comment='标题'),
    sa.Column('content', sa.Text(), nullable=False, comment='内容'),
    sa.Column('content_type', sa.String(length=50), nullable=False, comment='内容类型'),
    sa.Column('source_content_id', sa.Integer(), nullable=False, comment='原始内容ID'),
    sa.Column('format_config', sa.JSON(), nullable=False, comment='格式配置'),
    sa.Column('generation_config', sa.JSON(), nullable=False, comment='生成配置'),
    sa.Column('prompt_used', sa.Text(), nullable=False, comment='使用的提示词'),
    sa.Column('model_used', sa.String(length=100), nullable=False, comment='使用的模型'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='更新时间'),
    sa.ForeignKeyConstraint(['source_content_id'], ['contents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('report_contents',
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.Column('content_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
    sa.PrimaryKeyConstraint('report_id', 'content_id')
    )
    op.drop_index('ix_content_platform_id', table_name='content')
    op.drop_index('ix_content_publish_time', table_name='content')
    op.drop_index('ix_content_status', table_name='content')
    op.drop_table('content')
    op.drop_table('content_tag')
    op.drop_index('ix_tag_name', table_name='tag')
    op.drop_table('tag')
    op.drop_index('ix_comment_content_id', table_name='comment')
    op.drop_index('ix_comment_parent_id', table_name='comment')
    op.drop_index('ix_comment_publish_time', table_name='comment')
    op.drop_index('ix_comment_status', table_name='comment')
    op.drop_table('comment')
    op.drop_index('ix_platform_name', table_name='platform')
    op.drop_table('platform')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('platform',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), nullable=False),
    sa.Column('description', sa.VARCHAR(length=200), nullable=True),
    sa.Column('base_url', sa.VARCHAR(length=200), nullable=False),
    sa.Column('enabled', sa.BOOLEAN(), nullable=False),
    sa.Column('config', sqlite.JSON(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index('ix_platform_name', 'platform', ['name'], unique=False)
    op.create_table('comment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('content_id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.INTEGER(), nullable=True),
    sa.Column('author', sa.VARCHAR(length=100), nullable=True),
    sa.Column('text', sa.TEXT(), nullable=False),
    sa.Column('publish_time', sa.DATETIME(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=False),
    sa.Column('stats', sqlite.JSON(), nullable=True),
    sa.Column('metadata', sqlite.JSON(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['comment.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comment_status', 'comment', ['status'], unique=False)
    op.create_index('ix_comment_publish_time', 'comment', ['publish_time'], unique=False)
    op.create_index('ix_comment_parent_id', 'comment', ['parent_id'], unique=False)
    op.create_index('ix_comment_content_id', 'comment', ['content_id'], unique=False)
    op.create_table('tag',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), nullable=False),
    sa.Column('description', sa.VARCHAR(length=200), nullable=True),
    sa.Column('parent_id', sa.INTEGER(), nullable=True),
    sa.Column('weight', sa.FLOAT(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['tag.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index('ix_tag_name', 'tag', ['name'], unique=False)
    op.create_table('content_tag',
    sa.Column('content_id', sa.INTEGER(), nullable=False),
    sa.Column('tag_id', sa.INTEGER(), nullable=False),
    sa.Column('weight', sa.FLOAT(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('content_id', 'tag_id')
    )
    op.create_table('content',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('platform_id', sa.INTEGER(), nullable=False),
    sa.Column('url', sa.VARCHAR(length=500), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('summary', sa.TEXT(), nullable=True),
    sa.Column('content', sa.TEXT(), nullable=True),
    sa.Column('content_type', sa.VARCHAR(length=20), nullable=False),
    sa.Column('author', sa.VARCHAR(length=100), nullable=True),
    sa.Column('publish_time', sa.DATETIME(), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=False),
    sa.Column('quality_score', sa.FLOAT(), nullable=True),
    sa.Column('stats', sqlite.JSON(), nullable=True),
    sa.Column('metadata', sqlite.JSON(), nullable=True),
    sa.Column('media', sqlite.JSON(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['platform_id'], ['platform.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_index('ix_content_status', 'content', ['status'], unique=False)
    op.create_index('ix_content_publish_time', 'content', ['publish_time'], unique=False)
    op.create_index('ix_content_platform_id', 'content', ['platform_id'], unique=False)
    op.drop_table('report_contents')
    op.drop_table('generated_contents')
    op.drop_table('content_tags')
    op.drop_table('comments')
    op.drop_table('contents')
    op.drop_table('tags')
    op.drop_table('reports')
    op.drop_table('platforms')
    # ### end Alembic commands ### 