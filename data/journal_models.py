"""
Journal quality data models and storage.

Data sources:
- Scimago Journal Rank (SJR) - https://www.scimagojr.com/journalrank.php
  - Provides Q1-Q4 quartile rankings per subject area
  - Freely available as CSV export
- DOAJ (Directory of Open Access Journals) - https://doaj.org/
  - Legitimate open access journals
  - API available for validation
- Beall's List (predatory journals) - https://beallslist.net/
  - Criteria-based predatory journal detection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class JournalQuartile(Enum):
    """Journal quartile based on Scimago Journal Rank (SJR)."""

    Q1 = "Q1"  # Top 25% in subject area
    Q2 = "Q2"  # 25-50%
    Q3 = "Q3"  # 50-75%
    Q4 = "Q4"  # Bottom 25%
    UNKNOWN = "UNKNOWN"


class JournalType(Enum):
    """Journal publication type."""

    JOURNAL = "journal"
    CONFERENCE = "conference"
    BOOK_SERIES = "book_series"
    TRADE_JOURNAL = "trade_journal"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class JournalRecord:
    """
    Single journal record from Scimago or similar source.

    Attributes:
        issn: Primary ISSN (print or electronic)
        issn_print: Print ISSN (optional)
        issn_electronic: Electronic ISSN (optional)
        title: Journal title
        publisher: Publisher name
        subject_area: Scimago subject area code
        quartile: Q1-Q4 ranking
        sjr: Scimago Journal Rank score (year-specific)
        h_index: H-index
        cite_score: CiteScore
        impact_factor: Journal Impact Factor (JCR)
        is_open_access: Whether journal is open access
        country: Country of publication
        languages: Publication languages
        website: Official journal website
    """

    issn: str
    title: str
    publisher: str = ""
    subject_area: str = ""
    quartile: JournalQuartile = JournalQuartile.UNKNOWN
    sjr: float = 0.0
    h_index: int = 0
    cite_score: float = 0.0
    impact_factor: float = 0.0
    is_open_access: bool = False
    country: str = ""
    languages: tuple[str, ...] = ()
    website: str = ""
    issn_print: str = ""
    issn_electronic: str = ""
    year: int = 0  # Year of SJR data

    def __post_init__(self):
        """Validate ISSN format after initialization."""
        # ISSN format: 4 digits + hyphen + 4 digits (or 8 digits without hyphen)
        import re

        issn_pattern = re.compile(r"^\d{4}-?\d{3}[\dX]$")

        if self.issn and not issn_pattern.match(self.issn):
            raise ValueError(f"Invalid ISSN format: {self.issn}")
        if self.issn_print and not issn_pattern.match(self.issn_print):
            raise ValueError(f"Invalid print ISSN format: {self.issn_print}")
        if self.issn_electronic and not issn_pattern.match(self.issn_electronic):
            raise ValueError(f"Invalid electronic ISSN format: {self.issn_electronic}")


@dataclass
class JournalQualityStats:
    """Aggregate statistics for journal quality scoring."""

    total_journals: int = 0
    q1_count: int = 0
    q2_count: int = 0
    q3_count: int = 0
    q4_count: int = 0
    unknown_count: int = 0
    open_access_count: int = 0
    avg_sjr: float = 0.0
    avg_h_index: float = 0.0
    avg_cite_score: float = 0.0
    subject_areas: tuple[str, ...] = ()


@dataclass
class PredatoryJournalCriteria:
    """
    Beall's List criteria for predatory journal detection.

    Based on: https://beallslist.net/standards/

    NOTE: This is NOT an exhaustive list. The criteria are evolving
    and should be regularly updated.
    """

    # Naming patterns often used by predatory journals
    suspicious_name_patterns: tuple[str, ...] = (
        "international journal of advances in",
        "global journal of",
        "journal of emerging technologies",
        "world journal of",
        "american journal of",
        "european journal of",
        "journal of scientific",
        "international research journal of",
        "journal of advanced research in",
        "journal of applied science and",
        "international journal of innovative",
        "journal of multidisciplinary",
        "journal of engineering and",
        "international conference on",
    )

    # Red flags in publisher name
    suspicious_publisher_patterns: tuple[str, ...] = (
        "academic emporium",
        "open access publishing",
        "science publishing group",
        "international publication house",
        "global research foundation",
    )

    # Red flags in website domain
    suspicious_domain_patterns: tuple[str, ...] = (
        "-journal.com",
        "-journal.org",
        "-research.org",
        "-science.org",
        "-publishing.com",
        "-press.com",
    )

    # Minimum expected metrics (journals below these are suspicious)
    min_h_index: int = 10
    min_sjr: float = 0.1
    min_cite_score: float = 0.5
