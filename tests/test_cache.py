from vogue.sources.base import PageCache


def test_cache_roundtrip(tmp_path):
    cache = PageCache(tmp_path)
    calls = []

    def fetch():
        calls.append(1)
        return "<html>hi</html>"

    a = cache.get_or_fetch("gepris", "repair", 0, fetch)
    b = cache.get_or_fetch("gepris", "repair", 0, fetch)
    assert a == b == "<html>hi</html>"
    assert len(calls) == 1  # second call served from disk
    assert (tmp_path / "gepris").exists()
