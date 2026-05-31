from schemas.paper import AuthorDTO, PaperDTO
from utils.export import export_bibtex, export_csv, export_json


def _sample_papers() -> list[PaperDTO]:
    return [
        PaperDTO(
            title="Attention Is All You Need",
            authors=[AuthorDTO(name="Ashish Vaswani"), AuthorDTO(name="Noam Shazeer")],
            abstract="We propose a new simple network architecture...",
            year=2017,
            venue="NIPS",
            doi="10.1234/attention",
            source="arxiv",
            sources=["arxiv"],
            is_open_access=True,
            oa_url="https://arxiv.org/pdf/1706.03762.pdf",
            landing_url="https://arxiv.org/abs/1706.03762",
            topics=["deep learning", "nlp"],
            citation_count=42,
        ),
        PaperDTO(
            title="Deep Residual Learning",
            authors=[AuthorDTO(name="Kaiming He")],
            year=2016,
            venue="CVPR",
            doi="10.1234/resnet",
            source="crossref",
            sources=["crossref"],
            is_open_access=False,
            topics=["computer vision"],
        ),
    ]


def test_export_bibtex() -> None:
    papers = _sample_papers()
    bib = export_bibtex(papers)
    assert "@article{vaswani2017," in bib
    assert "title = {Attention Is All You Need}" in bib
    assert "author = {Vaswani, Ashish and Shazeer, Noam}" in bib
    assert "journal = {NIPS}" in bib
    assert "year = {2017}" in bib
    assert "doi = {10.1234/attention}" in bib
    assert "@article{he2016," in bib


def test_export_csv() -> None:
    papers = _sample_papers()
    csv_text = export_csv(papers)
    lines = csv_text.strip().split("\n")
    assert len(lines) == 3  # header + 2 rows
    assert "title,authors,year,venue" in lines[0]
    assert "Attention Is All You Need" in lines[1]
    assert "Deep Residual Learning" in lines[2]


def test_export_json() -> None:
    papers = _sample_papers()
    json_text = export_json(papers)
    import json

    data = json.loads(json_text)
    assert len(data) == 2
    assert data[0]["title"] == "Attention Is All You Need"
    assert data[1]["title"] == "Deep Residual Learning"
