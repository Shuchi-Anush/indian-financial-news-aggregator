from app.domain.articles import RawArticle
from app.processors.normalizer import ArticleNormalizer, compute_content_hash

def test_article_normalizer():
    raw = RawArticle(
        source_id="123e4567-e89b-12d3-a456-426614174000",
        source_name="Example Source",
        url="https://example.com/test",
        title="  Test Title  ",
        content="<p>Test content</p><script>alert(1)</script>",
        published_at_raw="2026-06-21T12:00:00Z",
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
