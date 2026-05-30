from utils.normalize import normalize_arxiv_id, normalize_doi, normalize_title


def test_normalize_doi() -> None:
    assert normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"


def test_normalize_arxiv_id_removes_version() -> None:
    assert normalize_arxiv_id("arXiv:2301.12345v3") == "2301.12345"


def test_normalize_title() -> None:
    assert normalize_title("Graph Neural Networks: A Survey!") == "graph neural networks a survey"
