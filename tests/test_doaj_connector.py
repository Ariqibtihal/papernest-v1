from connectors.doaj import DoajConnector
from schemas.paper import PaperDTO

MINIMAL_DOAJ_RESPONSE = {
    "bibjson": {
        "title": "Open Access Research in DOAJ",
        "abstract": "This paper explores open access publishing.",
        "year": "2022",
        "month": "03",
        "author": [{"name": "Jane Doe"}, {"name": "John Smith"}],
        "identifier": [
            {"type": "doi", "id": "10.1234/doaj.example"},
            {"type": "pissn", "id": "1234-5678"},
        ],
        "link": [{"type": "fulltext", "url": "https://example.com/article.pdf"}],
        "journal": {
            "title": "Journal of Open Access",
            "publisher": "OA Publisher Ltd",
            "issns": ["1234-5678"],
        },
        "subject": [{"term": "Open Access"}, {"term": "Publishing"}],
        "keywords": ["open access", "publishing"],
    }
}


def test_doaj_normalize() -> None:
    conn = DoajConnector()
    paper = conn.normalize(MINIMAL_DOAJ_RESPONSE)
    assert paper is not None
    assert isinstance(paper, PaperDTO)
    assert paper.title == "Open Access Research in DOAJ"
    assert paper.abstract == "This paper explores open access publishing."
    assert paper.year == 2022
    assert paper.publication_date is not None
    assert paper.publication_date.year == 2022
    assert paper.publication_date.month == 3
    assert paper.doi == "10.1234/doaj.example"
    assert paper.venue_issn == "1234-5678"
    assert paper.source == "doaj"
    assert paper.sources == ["doaj"]
    assert paper.venue == "Journal of Open Access"
    assert paper.publisher == "OA Publisher Ltd"
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "https://example.com/article.pdf"
    assert len(paper.authors) == 2
    assert paper.authors[0].name == "Jane Doe"
    assert paper.authors[1].name == "John Smith"
    assert "Open Access" in paper.topics
    assert "Publishing" in paper.topics
    assert "open access" in paper.topics


def test_doaj_normalize_no_month() -> None:
    conn = DoajConnector()
    data = MINIMAL_DOAJ_RESPONSE.copy()
    data["bibjson"] = {**data["bibjson"], "month": None}
    paper = conn.normalize(data)
    assert paper is not None
    assert paper.publication_date is not None
    assert paper.publication_date.month == 1
