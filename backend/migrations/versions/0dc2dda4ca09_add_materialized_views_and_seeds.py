"""add_materialized_views_and_seeds

Revision ID: 0dc2dda4ca09
Revises: 21af7d79c2f7
Create Date: 2026-06-16 20:24:10.985186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dc2dda4ca09'
down_revision: Union[str, Sequence[str], None] = '21af7d79c2f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_trends_mv AS
        SELECT 
            ae.entity,
            ae.entity_type,
            date_trunc('hour', a.published_at) AS time_bucket,
            count(*) AS article_count
        FROM article_entities ae
        JOIN articles a ON ae.article_id = a.id
        WHERE a.published_at IS NOT NULL
        GROUP BY ae.entity, ae.entity_type, date_trunc('hour', a.published_at)
        WITH NO DATA;
    """)

    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS sentiment_summaries_mv AS
        SELECT
            date_trunc('day', a.published_at) AS date_bucket,
            COALESCE(a.sentiment_label, 'NEUTRAL') AS sentiment_label,
            count(*) AS article_count
        FROM articles a
        WHERE a.published_at IS NOT NULL
        GROUP BY date_trunc('day', a.published_at), COALESCE(a.sentiment_label, 'NEUTRAL')
        WITH NO DATA;
    """)

    op.execute("""
        INSERT INTO feed_sources (id, name, slug, url, source_type, timezone_hint, is_active) VALUES
        (gen_random_uuid(), 'Economic Times Markets', 'economic-times-markets', 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms', 'RSS', 'Asia/Kolkata', true),
        (gen_random_uuid(), 'LiveMint Markets', 'livemint-markets', 'https://www.livemint.com/rss/markets', 'RSS', 'Asia/Kolkata', true),
        (gen_random_uuid(), 'Business Standard Markets', 'business-standard-markets', 'https://www.business-standard.com/rss/markets-106.rss', 'RSS', 'Asia/Kolkata', true),
        (gen_random_uuid(), 'Moneycontrol Markets', 'moneycontrol-markets', 'https://www.moneycontrol.com/rss/marketreports.xml', 'RSS', 'Asia/Kolkata', true),
        (gen_random_uuid(), 'SEBI Press Releases', 'sebi-press-releases', 'https://www.sebi.gov.in/sebirss.xml', 'RSS', 'Asia/Kolkata', true)
        ON CONFLICT (slug) DO UPDATE 
        SET url = EXCLUDED.url, is_active = EXCLUDED.is_active;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS sentiment_summaries_mv;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS hourly_trends_mv;")
