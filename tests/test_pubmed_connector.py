from connectors.pubmed import PubmedConnector
from schemas.paper import PaperDTO

PUBMED_ARTICLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticle>
  <MedlineCitation Status="PubMed-not-MEDLINE">
    <Article PubModel="Print-Electronic">
      <ArticleTitle>Deep Learning in Medical Imaging</ArticleTitle>
      <Abstract>
        <AbstractText Label="BACKGROUND">Medical imaging is evolving.</AbstractText>
        <AbstractText Label="METHODS">We used CNNs.</AbstractText>
        <AbstractText Label="RESULTS">Results were excellent.</AbstractText>
      </Abstract>
      <AuthorList>
        <Author ValidYN="Y">
          <LastName>LeCun</LastName>
          <ForeName>Yann</ForeName>
          <Initials>Y</Initials>
          <AffiliationInfo>
            <Affiliation>NYU</Affiliation>
          </AffiliationInfo>
        </Author>
        <Author ValidYN="Y">
          <LastName>Bengio</LastName>
          <ForeName>Yoshua</ForeName>
          <Initials>Y</Initials>
        </Author>
      </AuthorList>
      <Journal>
        <ISSN>1234-5678</ISSN>
        <Title>Journal of AI Medicine</Title>
        <ISOAbbreviation>J AI Med</ISOAbbreviation>
        <JournalIssue>
          <PubDate>
            <Year>2022</Year>
            <Month>May</Month>
            <Day>15</Day>
          </PubDate>
        </JournalIssue>
      </Journal>
      <ELocationID EIdType="doi">10.1234/pubmed.example</ELocationID>
    </Article>
    <ArticleIdList>
      <ArticleId IdType="pubmed">33333333</ArticleId>
      <ArticleId IdType="pmc">PMC9999999</ArticleId>
      <ArticleId IdType="doi">10.1234/pubmed.example</ArticleId>
    </ArticleIdList>
    <MeshHeadingList>
      <MeshHeading>
        <DescriptorName>Deep Learning</DescriptorName>
      </MeshHeading>
      <MeshHeading>
        <DescriptorName>Medical Imaging</DescriptorName>
      </MeshHeading>
    </MeshHeadingList>
    <KeywordList Owner="NLM">
      <Keyword>AI</Keyword>
      <Keyword>Radiology</Keyword>
    </KeywordList>
  </MedlineCitation>
</PubmedArticle>
"""


def test_pubmed_normalize() -> None:
    conn = PubmedConnector()
    paper = conn.normalize(PUBMED_ARTICLE_XML)
    assert paper is not None
    assert isinstance(paper, PaperDTO)
    assert paper.title == "Deep Learning in Medical Imaging"
    assert "BACKGROUND: Medical imaging is evolving." in paper.abstract
    assert "METHODS: We used CNNs." in paper.abstract
    assert "RESULTS: Results were excellent." in paper.abstract
    assert paper.year == 2022
    assert paper.publication_date is not None
    assert paper.publication_date.month == 5
    assert paper.publication_date.day == 15
    assert paper.doi == "10.1234/pubmed.example"
    assert paper.pubmed_id == "33333333"
    assert paper.source == "pubmed"
    assert paper.sources == ["pubmed"]
    assert paper.venue == "Journal of AI Medicine"
    assert paper.venue_issn == "1234-5678"
    assert paper.is_open_access is True
    assert str(paper.oa_url) == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9999999/pdf/"
    assert str(paper.landing_url) == "https://pubmed.ncbi.nlm.nih.gov/33333333/"
    assert len(paper.authors) == 2
    assert paper.authors[0].name == "Yann LeCun"
    assert paper.authors[0].affiliation == "NYU"
    assert paper.authors[1].name == "Yoshua Bengio"
    assert paper.authors[1].affiliation is None
    assert "Deep Learning" in paper.topics
    assert "Medical Imaging" in paper.topics
    assert "AI" in paper.topics
    assert "Radiology" in paper.topics


def test_pubmed_normalize_no_pmcid() -> None:
    conn = PubmedConnector()
    xml = PUBMED_ARTICLE_XML.replace('IdType="pmc">PMC9999999', 'IdType="pmc">')
    xml = xml.replace(">PMC9999999<", "><")
    paper = conn.normalize(xml)
    assert paper is not None
    assert paper.is_open_access is False
    assert paper.oa_url is None
