from schemas.paper import PaperDTO
from services.ranking_service import RankingService


def test_ranking_assigns_final_score() -> None:
    paper = PaperDTO(
        title="Graph Neural Networks for Drug Discovery",
        source="test",
        year=2024,
        citation_count=100,
        venue="Nature Machine Intelligence",
        is_open_access=True,
    )
    scored = RankingService.score_one(paper, "graph neural network drug discovery")
    assert scored.final_score is not None
    assert 0 <= scored.final_score <= 1
