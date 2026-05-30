from connectors.core import CoreConnector


def test_core_normalize_basic_work() -> None:
    raw = {
        "title": "Open Access Research from Institutional Repositories",
        "authors": [
            {"name": "Jane Doe", "affiliation": "University of Indonesia"},
            {"name": "John Smith"},
        ],
        "abstract": "A study about institutional repositories.",
        "yearPublished": 2023,
        "doi": "https://doi.org/10.1234/core.2023.1",
        "publisher": "Repository Journal",
        "citationCount": 12,
        "downloadUrl": "https://example.edu/paper.pdf",
        "topics": ["open access", "repositories"],
    }

    paper = CoreConnector().normalize(raw)

    assert paper is not None
    assert paper.title == "Open Access Research from Institutional Repositories"
    assert [author.name for author in paper.authors] == ["Jane Doe", "John Smith"]
    assert paper.authors[0].affiliation == "University of Indonesia"
    assert paper.year == 2023
    assert paper.doi == "10.1234/core.2023.1"
    assert paper.source == "core"
    assert paper.sources == ["core"]
    assert paper.venue == "Repository Journal"
    assert paper.citation_count == 12
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "https://example.edu/paper.pdf"
    assert paper.topics == ["open access", "repositories"]


def test_core_normalize_identifier_doi_and_date_year() -> None:
    raw = {
        "title": ["CORE Metadata Example"],
        "authors": ["Alice Example"],
        "publishedDate": "2021-05-10",
        "identifiers": [{"type": "doi", "identifier": "doi:10.5555/example"}],
        "fullTextLinks": [{"url": "https://repo.example.ac.id/fulltext.pdf"}],
        "subjects": [{"name": "computer science"}],
    }

    paper = CoreConnector().normalize(raw)

    assert paper is not None
    assert paper.title == "CORE Metadata Example"
    assert paper.year == 2021
    assert paper.doi == "10.5555/example"
    assert str(paper.oa_url) == "https://repo.example.ac.id/fulltext.pdf"
    assert paper.topics == ["computer science"]


def test_core_normalize_missing_title_returns_none() -> None:
    assert CoreConnector().normalize({"authors": ["No Title"]}) is None
