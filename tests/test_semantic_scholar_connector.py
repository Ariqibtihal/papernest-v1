from connectors.semantic_scholar import SemanticScholarConnector
from schemas.paper import PaperDTO

MINIMAL_SS_RESPONSE = {
    "paperId": "abc123",
    "externalIds": {"DOI": "10.1234/example", "ArXiv": "2301.00001"},
    "title": "Example Paper Title",
    "abstract": "This is an example abstract.",
    "year": 2023,
    "venue": "Example Conference",
    "publicationDate": "2023-06-15",
    "citationCount": 42,
    "referenceCount": 20,
    "influentialCitationCount": 5,
    "isOpenAccess": True,
    "openAccessPdf": {"url": "https://pdf.example.com/paper.pdf", "status": "GREEN"},
    "fieldsOfStudy": ["Computer Science", "Machine Learning"],
    "authors": [
        {"name": "Alice Researcher", "authorId": "a1"},
        {"name": "Bob Scientist", "authorId": "b2"},
    ],
    "url": "https://semanticscholar.org/paper/abc123",
    "journal": {"name": "Example Journal", "publisher": "Example Publisher"},
}


def test_semantic_scholar_normalize() -> None:
    conn = SemanticScholarConnector()
    paper = conn.normalize(MINIMAL_SS_RESPONSE)
    assert isinstance(paper, PaperDTO)
    assert paper.title == "Example Paper Title"
    assert paper.abstract == "This is an example abstract."
    assert paper.year == 2023
    assert paper.publication_date is not None
    assert paper.publication_date.year == 2023
    assert paper.doi == "10.1234/example"
    assert paper.arxiv_id == "2301.00001"
    assert paper.pubmed_id is None
    assert paper.source == "semantic_scholar"
    assert paper.sources == ["semantic_scholar"]
    assert paper.venue == "Example Conference"
    assert paper.publisher == "Example Publisher"
    assert paper.citation_count == 42
    assert paper.reference_count == 20
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "https://pdf.example.com/paper.pdf"
    assert str(paper.landing_url) == "https://semanticscholar.org/paper/abc123"
    assert len(paper.authors) == 2
    assert paper.authors[0].name == "Alice Researcher"
    assert paper.authors[1].name == "Bob Scientist"
    assert "Computer Science" in paper.topics
    assert "Machine Learning" in paper.topics


def test_semantic_scholar_normalize_journal_fallback_venue() -> None:
    conn = SemanticScholarConnector()
    data = MINIMAL_SS_RESPONSE.copy()
    data["venue"] = None
    data["journal"] = {"name": "Fallback Journal"}
    paper = conn.normalize(data)
    assert paper.venue == "Fallback Journal"
