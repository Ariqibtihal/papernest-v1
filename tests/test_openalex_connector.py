from connectors.openalex import OpenAlexConnector


def test_openalex_normalize_minimal_work() -> None:
    raw = {
        "id": "https://openalex.org/W123",
        "doi": "https://doi.org/10.1000/example",
        "title": "Graph Neural Networks for Drug Discovery",
        "publication_year": 2024,
        "publication_date": "2024-05-01",
        "cited_by_count": 123,
        "referenced_works": ["W1", "W2"],
        "abstract_inverted_index": {"Graph": [0], "networks": [1], "help": [2], "discovery": [3]},
        "authorships": [
            {
                "author": {"display_name": "Jane Smith", "orcid": "https://orcid.org/0000-0000"},
                "institutions": [{"display_name": "Example University"}],
            }
        ],
        "primary_location": {
            "landing_page_url": "https://example.org/article",
            "source": {
                "display_name": "Nature Machine Intelligence",
                "issn": ["1234-5678"],
                "host_organization_name": "Nature Portfolio",
            },
        },
        "open_access": {"is_oa": True},
        "best_oa_location": {"pdf_url": "https://example.org/paper.pdf"},
        "concepts": [{"display_name": "Artificial Intelligence"}],
    }

    paper = OpenAlexConnector().normalize(raw)

    assert paper.title == "Graph Neural Networks for Drug Discovery"
    assert paper.doi == "10.1000/example"
    assert paper.year == 2024
    assert paper.citation_count == 123
    assert paper.is_open_access is True
    assert paper.oa_url is not None
    assert paper.venue == "Nature Machine Intelligence"
    assert paper.authors[0].affiliation == "Example University"
    assert paper.abstract == "Graph networks help discovery"
