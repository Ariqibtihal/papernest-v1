from connectors.arxiv import ArxivConnector
from schemas.paper import PaperDTO

ARXIV_ENTRY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>Attention Is All You Need</title>
  <id>http://arxiv.org/abs/1706.03762</id>
  <published>2017-06-12T00:00:00Z</published>
  <updated>2021-09-28T00:00:00Z</updated>
  <summary>We propose a new simple network architecture...</summary>
  <author>
    <name>Ashish Vaswani</name>
    <arxiv:affiliation>Google Brain</arxiv:affiliation>
  </author>
  <author>
    <name>Noam Shazeer</name>
  </author>
  <arxiv:comment>19 pages, 5 figures</arxiv:comment>
  <link href="http://arxiv.org/abs/1706.03762" rel="alternate" type="text/html"/>
  <link title="pdf" href="http://arxiv.org/pdf/1706.03762.pdf" rel="related" type="application/pdf"/>
  <arxiv:primary_category term="cs.CL"/>
  <category term="cs.CL"/>
  <category term="cs.LG"/>
  <category term="cs.AI"/>
</entry>
"""


def test_arxiv_normalize() -> None:
    conn = ArxivConnector()
    paper = conn.normalize(ARXIV_ENTRY_XML)
    assert paper is not None
    assert isinstance(paper, PaperDTO)
    assert paper.title == "Attention Is All You Need"
    assert paper.abstract == "We propose a new simple network architecture..."
    assert paper.year == 2017
    assert paper.arxiv_id == "1706.03762"
    assert paper.source == "arxiv"
    assert paper.sources == ["arxiv"]
    assert paper.venue == "arXiv"
    assert paper.publisher == "arXiv"
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "http://arxiv.org/pdf/1706.03762.pdf"
    assert str(paper.landing_url) == "http://arxiv.org/abs/1706.03762"
    assert len(paper.authors) == 2
    assert paper.authors[0].name == "Ashish Vaswani"
    assert paper.authors[0].affiliation == "Google Brain"
    assert paper.authors[1].name == "Noam Shazeer"
    assert paper.authors[1].affiliation is None
    assert "cs.CL" in paper.topics
    assert "cs.LG" in paper.topics
    assert "cs.AI" in paper.topics
