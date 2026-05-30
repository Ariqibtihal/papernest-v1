from connectors.europepmc import EuropePmcConnector
from schemas.paper import PaperDTO

MINIMAL_EUROPEPMC_RESPONSE = {
    "id": "12345678",
    "source": "MED",
    "pmid": "12345678",
    "pmcid": "PMC1234567",
    "doi": "10.1234/europepmc.example",
    "title": "Europe PMC Example Paper",
    "authorString": "Smith J, Doe A",
    "journalTitle": "Journal of Biomedicine",
    "pubYear": "2023",
    "pageInfo": "1-10",
    "abstractText": "This is an example abstract from Europe PMC.",
    "isOpenAccess": "Y",
    "inEPMC": "Y",
    "hasPDF": "Y",
    "pubType": "journal article",
}


def test_europepmc_normalize() -> None:
    conn = EuropePmcConnector()
    paper = conn.normalize(MINIMAL_EUROPEPMC_RESPONSE)
    assert isinstance(paper, PaperDTO)
    assert paper.title == "Europe PMC Example Paper"
    assert paper.abstract == "This is an example abstract from Europe PMC."
    assert paper.year == 2023
    assert paper.publication_date is not None
    assert paper.publication_date.year == 2023
    assert paper.doi == "10.1234/europepmc.example"
    assert paper.pubmed_id == "12345678"
    assert paper.source == "europepmc"
    assert paper.sources == ["europepmc"]
    assert paper.venue == "Journal of Biomedicine"
    assert paper.publisher is None
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "https://europepmc.org/articles/PMC1234567?pdf=render"
    assert str(paper.landing_url) == "https://europepmc.org/article/PMC/PMC1234567"
    assert len(paper.authors) == 2
    assert paper.authors[0].name == "Smith J"
    assert paper.authors[1].name == "Doe A"


def test_europepmc_normalize_no_pmcid() -> None:
    conn = EuropePmcConnector()
    data = MINIMAL_EUROPEPMC_RESPONSE.copy()
    data["pmcid"] = None
    data["hasPDF"] = "N"
    paper = conn.normalize(data)
    assert paper.oa_url is None
    assert str(paper.landing_url) == "https://europepmc.org/article/MED/12345678"
