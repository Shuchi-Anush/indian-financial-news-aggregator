from app.domain.articles import CanonicalArticle
from app.domain.deduplication import DedupCandidate
from app.processors.deduplicator import Deduplicator
from datetime import datetime, timezone

def test_deduplicator():
    candidates = [
        DedupCandidate(url="http://example.com/1", content_hash="hash1"),
        DedupCandidate(url="http://example.com/2", content_hash="hash2")
    ]
    
    deduper = Deduplicator(candidates)
    
    # Duplicate by URL
    art1 = CanonicalArticle(
        title="1", url="http://example.com/1", source_id="source1", source_name="s",
        content_hash="newhash", collected_at=datetime.now(timezone.utc),
        content="", summary="", author="", published_at=None, category="default"
    )
    res1 = deduper.check_duplicate(art1)
    assert res1.is_duplicate
    
    # Duplicate by Hash
    art2 = CanonicalArticle(
        title="2", url="http://example.com/new", source_id="source1", source_name="s",
        content_hash="hash2", collected_at=datetime.now(timezone.utc),
        content="", summary="", author="", published_at=None, category="default"
    )
    res2 = deduper.check_duplicate(art2)
    assert res2.is_duplicate
    
    # Not duplicate
    art3 = CanonicalArticle(
        title="3", url="http://example.com/3", source_id="source1", source_name="s",
        content_hash="hash3", collected_at=datetime.now(timezone.utc),
        content="", summary="", author="", published_at=None, category="default"
    )
    res3 = deduper.check_duplicate(art3)
    assert not res3.is_duplicate
