from datetime import datetime, timezone, timedelta

from app.domain.articles import RawArticle
from app.processors.normalizer import ArticleNormalizer, compute_content_hash

def test_article_normalizer():
    # Use a timestamp 1 hour ago so the article is never "stale"
    recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw = RawArticle(
        source_id="123e4567-e89b-12d3-a456-426614174000",
        source_name="Example Source",
        url="https://example.com/test",
        title="  Test Title  ",
        content="<p>Test content</p><script>alert(1)</script>",
        published_at_raw=recent_time,
        author="John Doe"
    )
    
    canonical = ArticleNormalizer.normalize(raw)
    
    assert canonical is not None
    assert canonical.title == "Test Title"
    assert canonical.content == "Test content"
    assert canonical.url == "https://example.com/test"
    assert canonical.author == "John Doe"

def test_compute_content_hash():
    hash1 = compute_content_hash("Title", "Content")
    hash2 = compute_content_hash("Title", "Content")
    hash3 = compute_content_hash("Title", "Different")
    
    assert hash1 == hash2
    assert hash1 != hash3
