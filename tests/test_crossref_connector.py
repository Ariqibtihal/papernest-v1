from connectors.crossref import CrossrefConnector


def test_crossref_normalize_minimal_work() -> None:
    raw = {
        "DOI": "10.1000/example",
        "title": ["Graph Neural Networks for Drug Discovery"],
        "author": [{"given": "Jane", "family": "Smith", "ORCID": "https://orcid.org/0000-0000"}],
        "abstract": "This paper studies graph neural networks.",
        "issued": {"date-parts": [[2024, 5, 1]]},
        "container-title": ["Nature Machine Intelligence"],
        "publisher": "Example Publisher",
        "is-referenced-by-count": 42,
        "reference-count": 10,
        "URL": "https://doi.org/10.1000/example",
        "ISSN": ["1234-5678"],
        "subject": ["Artificial Intelligence"],
    }

    paper = CrossrefConnector().normalize(raw)

    assert paper.title == "Graph Neural Networks for Drug Discovery"
    assert paper.doi == "10.1000/example"
    assert paper.year == 2024
    assert paper.venue == "Nature Machine Intelligence"
    assert paper.citation_count == 42
    assert paper.authors[0].name == "Jane Smith"
    assert paper.sources == ["crossref"]
