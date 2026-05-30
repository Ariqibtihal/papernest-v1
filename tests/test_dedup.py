from schemas.paper import PaperDTO
from services.dedup_service import DedupService


def test_dedup_merges_crossref_and_openalex_by_doi() -> None:
    crossref = PaperDTO(
        title="Graph Neural Networks for Drug Discovery",
        source="crossref",
        sources=["crossref"],
        doi="10.1000/example",
        citation_count=10,
        is_open_access=False,
    )
    openalex = PaperDTO(
        title="Graph Neural Networks for Drug Discovery",
        source="openalex",
        sources=["openalex"],
        doi="https://doi.org/10.1000/example",
        citation_count=123,
        is_open_access=True,
        oa_url="https://example.org/paper.pdf",
    )

    results = DedupService().dedupe([crossref, openalex])

    assert len(results) == 1
    assert results[0].citation_count == 123
    assert results[0].is_open_access is True
    assert results[0].sources == ["crossref", "openalex"]
