"""Initial schema - all 32 tables for TREFF Post-Generator.

This baseline migration captures the complete database schema as of 2026-02-16.
It is designed to be stamped on existing databases (not run against them),
and to create all tables from scratch on new databases.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-02-16 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 32 tables for the TREFF Post-Generator."""

    # ── 1. users ──────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # ── 2. templates ──────────────────────────────────────────────────
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('platform_format', sa.String(), nullable=False),
        sa.Column('slide_count', sa.Integer(), default=1),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('css_content', sa.Text(), nullable=False),
        sa.Column('default_colors', sa.Text(), nullable=True),
        sa.Column('default_fonts', sa.Text(), nullable=True),
        sa.Column('placeholder_fields', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_country_themed', sa.Boolean(), default=False),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('parent_template_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 3. assets ─────────────────────────────────────────────────────
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(), default='upload'),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('file_data', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('thumbnail_path', sa.String(), nullable=True),
        sa.Column('thumbnail_small', sa.String(), nullable=True),
        sa.Column('thumbnail_medium', sa.String(), nullable=True),
        sa.Column('thumbnail_large', sa.String(), nullable=True),
        sa.Column('exif_data', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('marked_unused', sa.Integer(), nullable=True),
    )

    # ── 4. students ───────────────────────────────────────────────────
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('school_name', sa.String(), nullable=True),
        sa.Column('host_family_name', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('profile_image_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('fun_facts', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), default='active'),
        sa.Column('personality_preset', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_students_user_id', 'students', ['user_id'])
    op.create_index('ix_students_country', 'students', ['country'])
    op.create_index('ix_students_status', 'students', ['status'])

    # ── 5. story_arcs ─────────────────────────────────────────────────
    op.create_table(
        'story_arcs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('subtitle', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id'), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('status', sa.String(), default='draft'),
        sa.Column('planned_episodes', sa.Integer(), default=8),
        sa.Column('current_episode', sa.Integer(), default=0),
        sa.Column('cover_image_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=True),
        sa.Column('tone', sa.String(), default='jugendlich'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_story_arcs_user_id', 'story_arcs', ['user_id'])
    op.create_index('ix_story_arcs_student_id', 'story_arcs', ['student_id'])
    op.create_index('ix_story_arcs_country', 'story_arcs', ['country'])
    op.create_index('ix_story_arcs_status', 'story_arcs', ['status'])

    # ── 6. recurring_post_rules ───────────────────────────────────────
    op.create_table(
        'recurring_post_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source_post_id', sa.Integer(), nullable=False),  # FK added after posts table
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('time', sa.String(), default='10:00'),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('max_occurrences', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('generated_count', sa.Integer(), default=0),
        sa.Column('last_generated_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 7. posts ──────────────────────────────────────────────────────
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates.id'), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='draft'),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('slide_data', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('caption_instagram', sa.Text(), nullable=True),
        sa.Column('caption_tiktok', sa.Text(), nullable=True),
        sa.Column('hashtags_instagram', sa.Text(), nullable=True),
        sa.Column('hashtags_tiktok', sa.Text(), nullable=True),
        sa.Column('cta_text', sa.String(), nullable=True),
        sa.Column('custom_colors', sa.Text(), nullable=True),
        sa.Column('custom_fonts', sa.Text(), nullable=True),
        sa.Column('tone', sa.String(), default='jugendlich'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=True),
        sa.Column('scheduled_time', sa.String(), nullable=True),
        sa.Column('story_arc_id', sa.Integer(), sa.ForeignKey('story_arcs.id'), nullable=True),
        sa.Column('episode_number', sa.Integer(), nullable=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True),
        sa.Column('linked_post_group_id', sa.String(), nullable=True),
        sa.Column('recurring_rule_id', sa.Integer(), sa.ForeignKey('recurring_post_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_recurring_instance', sa.Integer(), nullable=True),
        sa.Column('perf_likes', sa.Integer(), nullable=True),
        sa.Column('perf_comments', sa.Integer(), nullable=True),
        sa.Column('perf_shares', sa.Integer(), nullable=True),
        sa.Column('perf_saves', sa.Integer(), nullable=True),
        sa.Column('perf_reach', sa.Integer(), nullable=True),
        sa.Column('perf_updated_at', sa.DateTime(), nullable=True),
        sa.Column('exported_at', sa.DateTime(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_posts_user_id', 'posts', ['user_id'])
    op.create_index('ix_posts_user_id_created_at', 'posts', ['user_id', 'created_at'])

    # ── 8. post_slides ────────────────────────────────────────────────
    op.create_table(
        'post_slides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slide_index', sa.Integer(), nullable=False),
        sa.Column('headline', sa.Text(), nullable=True),
        sa.Column('subheadline', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('bullet_points', sa.Text(), nullable=True),
        sa.Column('quote_text', sa.Text(), nullable=True),
        sa.Column('quote_author', sa.String(), nullable=True),
        sa.Column('cta_text', sa.String(), nullable=True),
        sa.Column('image_asset_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=True),
        sa.Column('background_type', sa.String(), nullable=True),
        sa.Column('background_value', sa.Text(), nullable=True),
        sa.Column('custom_css_overrides', sa.Text(), nullable=True),
    )

    # ── 9. story_episodes ─────────────────────────────────────────────
    op.create_table(
        'story_episodes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('arc_id', sa.Integer(), sa.ForeignKey('story_arcs.id'), nullable=False),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('episode_title', sa.String(), nullable=False),
        sa.Column('teaser_text', sa.Text(), nullable=True),
        sa.Column('cliffhanger_text', sa.Text(), nullable=True),
        sa.Column('previously_text', sa.Text(), nullable=True),
        sa.Column('next_episode_hint', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), default='planned'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_story_episodes_arc_id', 'story_episodes', ['arc_id'])
    op.create_index('ix_story_episodes_post_id', 'story_episodes', ['post_id'])
    op.create_index('ix_story_episodes_arc_id_episode_number', 'story_episodes', ['arc_id', 'episode_number'])

    # ── 10. calendar_entries ──────────────────────────────────────────
    op.create_table(
        'calendar_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.String(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 11. content_suggestions ───────────────────────────────────────
    op.create_table(
        'content_suggestions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('suggestion_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('suggested_category', sa.String(), nullable=True),
        sa.Column('suggested_country', sa.String(), nullable=True),
        sa.Column('suggested_date', sa.Date(), nullable=True),
        sa.Column('suggested_format', sa.String(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('accepted_post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # ── 12. export_history ────────────────────────────────────────────
    op.create_table(
        'export_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('resolution', sa.String(), nullable=True),
        sa.Column('slide_count', sa.Integer(), nullable=True),
        sa.Column('exported_at', sa.DateTime(), nullable=True),
    )

    # ── 13. settings ──────────────────────────────────────────────────
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.UniqueConstraint('user_id', 'key', name='uq_user_setting'),
    )

    # ── 14. hooks ─────────────────────────────────────────────────────
    op.create_table(
        'hooks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('hook_text', sa.Text(), nullable=False),
        sa.Column('hook_type', sa.String(50), nullable=False),
        sa.Column('topic', sa.String(200), nullable=True),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('selected', sa.Integer(), default=0),
        sa.Column('source', sa.String(50), default='rule_based'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_hooks_user_id', 'hooks', ['user_id'])
    op.create_index('ix_hooks_post_id', 'hooks', ['post_id'])

    # ── 15. humor_formats ─────────────────────────────────────────────
    op.create_table(
        'humor_formats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('template_structure', sa.Text(), nullable=False),
        sa.Column('example_text', sa.Text(), nullable=False),
        sa.Column('platform_fit', sa.String(), nullable=False, server_default='both'),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # ── 16. hashtag_sets ──────────────────────────────────────────────
    op.create_table(
        'hashtag_sets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('hashtags', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('performance_score', sa.Float(), default=0.0),
        sa.Column('is_default', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_hashtag_sets_user_id', 'hashtag_sets', ['user_id'])
    op.create_index('ix_hashtag_sets_category', 'hashtag_sets', ['category'])
    op.create_index('ix_hashtag_sets_country', 'hashtag_sets', ['country'])

    # ── 17. ctas ──────────────────────────────────────────────────────
    op.create_table(
        'ctas',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False, server_default='both'),
        sa.Column('format', sa.String(), nullable=False, server_default='all'),
        sa.Column('emoji', sa.String(), nullable=True),
        sa.Column('performance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # ── 18. post_interactive_elements ─────────────────────────────────
    op.create_table(
        'post_interactive_elements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slide_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('element_type', sa.String(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('correct_answer', sa.Integer(), nullable=True),
        sa.Column('emoji', sa.String(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('position_y', sa.Float(), nullable=False, server_default='50.0'),
    )
    op.create_index('ix_post_interactive_elements_post_id', 'post_interactive_elements', ['post_id'])

    # ── 19. series_reminders ──────────────────────────────────────────
    op.create_table(
        'series_reminders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('story_arc_id', sa.Integer(), sa.ForeignKey('story_arcs.id'), nullable=False),
        sa.Column('reminder_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('is_dismissed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_series_reminders_user_id', 'series_reminders', ['user_id'])
    op.create_index('ix_series_reminders_story_arc_id', 'series_reminders', ['story_arc_id'])
    op.create_index('ix_series_reminders_type', 'series_reminders', ['reminder_type'])
    op.create_index('ix_series_reminders_is_read', 'series_reminders', ['is_read'])

    # ── 20. video_overlays ────────────────────────────────────────────
    op.create_table(
        'video_overlays',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False, server_default='Unbenanntes Overlay'),
        sa.Column('layers', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('rendered_path', sa.String(), nullable=True),
        sa.Column('render_status', sa.String(), server_default='pending'),
        sa.Column('render_error', sa.Text(), nullable=True),
        sa.Column('rendered_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 21. music_tracks ──────────────────────────────────────────────
    op.create_table(
        'music_tracks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('mood', sa.String(), nullable=True),
        sa.Column('bpm', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=True),
        sa.Column('file_data', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # ── 22. video_templates ───────────────────────────────────────────
    op.create_table(
        'video_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='3.0'),
        sa.Column('width', sa.Integer(), nullable=False, server_default='1080'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='1920'),
        sa.Column('aspect_ratio', sa.String(), nullable=False, server_default='9:16'),
        sa.Column('branding_config', sa.Text(), nullable=True),
        sa.Column('style', sa.String(), nullable=False, server_default='default'),
        sa.Column('primary_color', sa.String(), nullable=False, server_default='#4C8BC2'),
        sa.Column('secondary_color', sa.String(), nullable=False, server_default='#FDD000'),
        sa.Column('social_handle_instagram', sa.String(), nullable=True),
        sa.Column('social_handle_tiktok', sa.String(), nullable=True),
        sa.Column('website_url', sa.String(), nullable=True),
        sa.Column('cta_text', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('preview_image_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 23. video_exports ─────────────────────────────────────────────
    op.create_table(
        'video_exports',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('assets.id'), nullable=False),
        sa.Column('aspect_ratio', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), server_default='instagram'),
        sa.Column('quality', sa.Integer(), server_default='75'),
        sa.Column('max_duration_seconds', sa.Float(), nullable=True),
        sa.Column('focus_x', sa.Float(), server_default='50.0'),
        sa.Column('focus_y', sa.Float(), server_default='50.0'),
        sa.Column('output_filename', sa.String(), nullable=True),
        sa.Column('output_path', sa.String(), nullable=True),
        sa.Column('output_file_size', sa.Integer(), nullable=True),
        sa.Column('output_width', sa.Integer(), nullable=True),
        sa.Column('output_height', sa.Integer(), nullable=True),
        sa.Column('output_duration', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('batch_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # ── 24. recurring_formats ─────────────────────────────────────────
    op.create_table(
        'recurring_formats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False, server_default='weekly'),
        sa.Column('preferred_day', sa.String(), nullable=True),
        sa.Column('preferred_time', sa.String(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('hashtags', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # ── 25. post_relations ────────────────────────────────────────────
    op.create_table(
        'post_relations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(), nullable=False, server_default='cross_reference'),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('source_post_id', 'target_post_id', name='uq_post_relation_pair'),
    )
    op.create_index('ix_post_relations_source_id', 'post_relations', ['source_post_id'])
    op.create_index('ix_post_relations_target_id', 'post_relations', ['target_post_id'])

    # ── 26. pipeline_items ────────────────────────────────────────────
    op.create_table(
        'pipeline_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True),
        sa.Column('asset_id', sa.Integer(), sa.ForeignKey('assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('suggested_post_type', sa.String(), nullable=True),
        sa.Column('suggested_caption_seeds', sa.Text(), nullable=True),
        sa.Column('suggested_platforms', sa.Text(), nullable=True),
        sa.Column('detected_country', sa.String(), nullable=True),
        sa.Column('analysis_summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('result_post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('source_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_pipeline_items_user_id', 'pipeline_items', ['user_id'])
    op.create_index('ix_pipeline_items_status', 'pipeline_items', ['status'])
    op.create_index('ix_pipeline_items_student_id', 'pipeline_items', ['student_id'])

    # ── 27. campaigns ─────────────────────────────────────────────────
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal', sa.String(), nullable=True),
        sa.Column('start_date', sa.String(), nullable=True),
        sa.Column('end_date', sa.String(), nullable=True),
        sa.Column('platforms', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_campaigns_user_id', 'campaigns', ['user_id'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])

    # ── 28. campaign_posts ────────────────────────────────────────────
    op.create_table(
        'campaign_posts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('scheduled_date', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='planned'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_campaign_posts_campaign_id', 'campaign_posts', ['campaign_id'])
    op.create_index('ix_campaign_posts_post_id', 'campaign_posts', ['post_id'])

    # ── 29. template_favorites ────────────────────────────────────────
    op.create_table(
        'template_favorites',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'template_id', name='uq_user_template_fav'),
    )

    # ── 30. video_scripts ─────────────────────────────────────────────
    op.create_table(
        'video_scripts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id'), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('hook_formula', sa.String(100), nullable=True),
        sa.Column('topic', sa.String(300), nullable=True),
        sa.Column('country', sa.String(50), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('buyer_journey_stage', sa.String(50), nullable=True),
        sa.Column('tone', sa.String(50), server_default='jugendlich'),
        sa.Column('scenes', sa.Text(), nullable=False),
        sa.Column('voiceover_full', sa.Text(), nullable=True),
        sa.Column('visual_notes', sa.Text(), nullable=True),
        sa.Column('cta_type', sa.String(50), nullable=True),
        sa.Column('source', sa.String(50), server_default='rule_based'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_video_scripts_user_id', 'video_scripts', ['user_id'])
    op.create_index('ix_video_scripts_post_id', 'video_scripts', ['post_id'])

    # ── 31. prompt_history ────────────────────────────────────────────
    op.create_table(
        'prompt_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('prompt_type', sa.String(50), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('result_text', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_prompt_history_user_id', 'prompt_history', ['user_id'])
    op.create_index('ix_prompt_history_prompt_type', 'prompt_history', ['prompt_type'])
    op.create_index('ix_prompt_history_is_favorite', 'prompt_history', ['is_favorite'])

    # ── 32. background_tasks ──────────────────────────────────────────
    op.create_table(
        'background_tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('task_type', sa.String(64), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('callback_url', sa.String(512), nullable=True),
    )
    op.create_index('ix_background_tasks_task_id', 'background_tasks', ['task_id'])


def downgrade() -> None:
    """Drop all 32 tables in reverse dependency order."""
    op.drop_table('background_tasks')
    op.drop_table('prompt_history')
    op.drop_table('video_scripts')
    op.drop_table('template_favorites')
    op.drop_table('campaign_posts')
    op.drop_table('campaigns')
    op.drop_table('pipeline_items')
    op.drop_table('post_relations')
    op.drop_table('recurring_formats')
    op.drop_table('video_exports')
    op.drop_table('video_templates')
    op.drop_table('music_tracks')
    op.drop_table('video_overlays')
    op.drop_table('series_reminders')
    op.drop_table('post_interactive_elements')
    op.drop_table('ctas')
    op.drop_table('hashtag_sets')
    op.drop_table('humor_formats')
    op.drop_table('hooks')
    op.drop_table('settings')
    op.drop_table('export_history')
    op.drop_table('content_suggestions')
    op.drop_table('calendar_entries')
    op.drop_table('story_episodes')
    op.drop_table('post_slides')
    op.drop_table('posts')
    op.drop_table('recurring_post_rules')
    op.drop_table('story_arcs')
    op.drop_table('students')
    op.drop_table('assets')
    op.drop_table('templates')
    op.drop_table('users')
