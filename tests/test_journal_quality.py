"""
Tests for Journal Quality Service.

These tests validate the journal quality scoring and predatory detection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from data.journal_models import JournalQuartile, JournalRecord
from services.journal_quality_service import JournalQualityService


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset JournalQualityService singleton before each test."""
    JournalQualityService.reset()
    yield
    JournalQualityService.reset()


@pytest.fixture
def sample_scimago_csv(tmp_path: Path) -> Path:
    """Create a sample Scimago CSV file for testing."""
    csv_content = """Rank;Sourceid;Title;Type;Issn;Publisher;Country;Categories;SJR;H index;CiteScore;Q1;Q2;Q3;Q4
1;12345;Nature;Journal;0028-0836;Springer Nature;United Kingdom;Multidisciplinary;14.148;844;66.2;1;0;0;0
2;23456;Science;Journal;0036-8075;American Association for the Advancement of Science;United States;Multidisciplinary;17.105;891;71.2;1;0;0;0
3;34567;Journal of Machine Learning Research;Journal;1532-4435;JMLR Inc;United States;Computer Science;4.521;234;12.3;1;0;0;0
4;45678;International Journal of Advances in Computing;Journal;2250-343X;Global Research Foundation;India;Computer Science;0.156;8;1.2;0;0;1;0
5;56789;PLoS ONE;Journal;1932-6203;Public Library of Science;United States;Multidisciplinary;1.234;312;4.5;0;1;0;0"""

    csv_path = tmp_path / "scimago_journals.csv"
    csv_path.write_text(csv_content, encoding="utf-8-sig")
    return csv_path


@pytest.fixture
def quality_service() -> JournalQualityService:
    """Create a fresh JournalQualityService for testing."""
    service = JournalQualityService()
    return service


class TestJournalModels:
    """Test journal data models."""

    def test_journal_quartile_enum(self):
        """Test JournalQuartile enum values."""
        assert JournalQuartile.Q1.value == "Q1"
        assert JournalQuartile.Q2.value == "Q2"
        assert JournalQuartile.Q3.value == "Q3"
        assert JournalQuartile.Q4.value == "Q4"
        assert JournalQuartile.UNKNOWN.value == "UNKNOWN"

    def test_journal_record_creation(self):
        """Test JournalRecord creation with valid ISSN."""
        record = JournalRecord(
            issn="1234-5678",
            title="Test Journal",
            publisher="Test Publisher",
            quartile=JournalQuartile.Q1,
            sjr=5.0,
            h_index=100,
        )
        assert record.issn == "1234-5678"
        assert record.title == "Test Journal"
        assert record.quartile == JournalQuartile.Q1
        assert record.sjr == 5.0

    def test_journal_record_invalid_issn(self):
        """Test JournalRecord creation with invalid ISSN raises error."""
        with pytest.raises(ValueError, match="Invalid ISSN format"):
            JournalRecord(
                issn="INVALID",
                title="Test Journal",
            )


class TestJournalQualityService:
    """Test JournalQualityService functionality."""

    @pytest.mark.asyncio
    async def test_load_scimago_csv(
        self, quality_service: JournalQualityService, sample_scimago_csv: Path
    ):
        """Test loading Scimago CSV file."""
        stats = await quality_service.load_data(scimago_csv_path=sample_scimago_csv)

        assert stats.total_journals == 5
        assert stats.q1_count == 3
        assert stats.q2_count == 1
        assert stats.q3_count == 1
        assert stats.q4_count == 0
        assert quality_service.is_loaded is True

    @pytest.mark.asyncio
    async def test_load_nonexistent_csv(self, quality_service: JournalQualityService):
        """Test loading non-existent CSV file."""
        stats = await quality_service.load_data(scimago_csv_path="/nonexistent/path.csv")

        assert stats.total_journals == 0
        assert quality_service.is_loaded is False

    def test_get_by_issn(self, quality_service: JournalQualityService):
        """Test ISSN lookup."""
        # Manually add a record
        record = JournalRecord(
            issn="12345678",
            title="Test Journal",
            quartile=JournalQuartile.Q1,
            sjr=5.0,
            h_index=100,
        )
        quality_service._records_by_issn["12345678"] = record

        # Test lookup
        found = quality_service.get_by_issn("1234-5678")
        assert found is not None
        assert found.title == "Test Journal"

    def test_get_by_title(self, quality_service: JournalQualityService):
        """Test title lookup."""
        # Add test records
        record1 = JournalRecord(
            issn="12345678",
            title="Journal of Machine Learning Research",
            quartile=JournalQuartile.Q1,
        )
        record2 = JournalRecord(
            issn="87654321",
            title="International Journal of Advanced Computing",
            quartile=JournalQuartile.Q3,
        )

        quality_service._records_by_issn["12345678"] = record1
        quality_service._records_by_issn["87654321"] = record2
        quality_service._title_index["journal of machine learning research"] = "12345678"
        quality_service._title_index["international journal of advanced computing"] = "87654321"

        # Test exact match
        found = quality_service.get_by_title("Journal of Machine Learning Research")
        assert found is not None
        assert found.issn == "12345678"

        # Test fuzzy match with token_set_ratio
        found = quality_service.get_by_title("Machine Learning Research Journal")
        assert found is not None

    def test_score_journal_known(self, quality_service: JournalQualityService):
        """Test journal scoring for known journal."""
        record = JournalRecord(
            issn="12345678",
            title="Nature",
            quartile=JournalQuartile.Q1,
            sjr=14.148,
            h_index=844,
            cite_score=66.2,
        )
        quality_service._records_by_issn["12345678"] = record
        quality_service._title_index["nature"] = "12345678"

        score = quality_service.score_journal(journal_title="Nature")
        assert 0.8 <= score <= 1.0  # Q1 journal with high metrics

    def test_score_journal_unknown(self, quality_service: JournalQualityService):
        """Test journal scoring for unknown journal."""
        score = quality_service.score_journal(journal_title="Unknown Journal")
        assert score == 0.5  # Neutral score for unknown

    def test_is_predatory_suspicious_name(self, quality_service: JournalQualityService):
        """Test predatory detection for suspicious journal name."""
        # Journal with suspicious name pattern (2+ red flags needed)
        result = quality_service.is_predatory(
            journal_title="International Journal of Advances in Computing Technology",
            publisher="Global Research Foundation",
        )
        assert result is True

    def test_is_predatory_legitimate(self, quality_service: JournalQualityService):
        """Test predatory detection for legitimate journal."""
        # Add a known legitimate journal
        record = JournalRecord(
            issn="12345678",
            title="Nature",
            quartile=JournalQuartile.Q1,
            sjr=14.148,
        )
        quality_service._records_by_issn["12345678"] = record

        result = quality_service.is_predatory(
            journal_title="Nature",
            issn="1234-5678",
        )
        assert result is False

    def test_normalize_issn(self, quality_service: JournalQualityService):
        """Test ISSN normalization."""
        assert quality_service._normalize_issn("1234-5678") == "12345678"
        assert quality_service._normalize_issn("12345678") == "12345678"
        assert quality_service._normalize_issn("1234-567X") == "1234567X"
        assert quality_service._normalize_issn("INVALID") == ""
        assert quality_service._normalize_issn("") == ""

    def test_normalize_title(self, quality_service: JournalQualityService):
        """Test title normalization."""
        assert quality_service._normalize_title("Nature") == "nature"
        assert quality_service._normalize_title("J. of ML Research") == "j of ml research"
        assert quality_service._normalize_title("  Multiple   Spaces  ") == "multiple spaces"


class TestPredatoryDetection:
    """Test predatory journal detection criteria."""

    def test_suspicious_name_patterns(self, quality_service: JournalQualityService):
        """Test detection of suspicious name patterns."""
        # Need 2+ red flags for predatory detection
        suspicious_cases = [
            ("International Journal of Advances in Computing", "Global Research Foundation"),
            ("Global Journal of Emerging Technologies", "Science Publishing Group"),
            ("Journal of Scientific Research", "Academic Emporium"),
            ("World Journal of Engineering", "International Publication House"),
        ]

        for name, publisher in suspicious_cases:
            result = quality_service.is_predatory(
                journal_title=name,
                publisher=publisher,
            )
            assert result is True, f"Should detect as predatory: {name}"

    def test_suspicious_publisher(self, quality_service: JournalQualityService):
        """Test detection of suspicious publishers."""
        result = quality_service.is_predatory(
            journal_title="International Journal of Advances in Computing",
            publisher="Academic Emporium Publishing",
        )
        assert result is True

    def test_suspicious_website(self, quality_service: JournalQualityService):
        """Test detection of suspicious website domains."""
        result = quality_service.is_predatory(
            journal_title="International Journal of Advances in Computing",
            publisher="Global Research Foundation",
            website="https://open-access-publishing.com",
        )
        assert result is True

    def test_known_journal_not_predatory(self, quality_service: JournalQualityService):
        """Test that known legitimate journals are not flagged."""
        # Add a known legitimate journal
        record = JournalRecord(
            issn="12345678",
            title="Journal of Machine Learning Research",
            quartile=JournalQuartile.Q1,
            sjr=4.521,
        )
        quality_service._records_by_issn["12345678"] = record

        result = quality_service.is_predatory(
            journal_title="Journal of Machine Learning Research",
            issn="1234-5678",
        )
        assert result is False

    def test_single_red_flag_not_predatory(self, quality_service: JournalQualityService):
        """Test that single red flag alone doesn't trigger predatory detection."""
        # Only suspicious name, no other red flags
        result = quality_service.is_predatory(
            journal_title="International Journal of Advances in Computing",
        )
        # Should NOT be predatory with just 1 red flag (threshold is 2)
        assert result is False


class TestIntegration:
    """Integration tests with sample data."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, sample_scimago_csv: Path):
        """Test complete workflow from loading to scoring."""
        service = JournalQualityService()
        await service.load_data(scimago_csv_path=sample_scimago_csv)

        # Verify stats
        stats = service.get_stats()
        assert stats.total_journals == 5
        assert stats.q1_count == 3

        # Test scoring
        nature_score = service.score_journal(journal_title="Nature")
        plos_score = service.score_journal(journal_title="PLoS ONE")

        # Nature (Q1) should score higher than PLoS ONE (Q2)
        assert nature_score > plos_score

        # Test predatory detection
        predatory = service.is_predatory(
            journal_title="International Journal of Advances in Computing",
            publisher="Global Research Foundation",
        )
        assert predatory is True
