"""
Deduplication Service for PaperLens

Provides multi-tier deduplication:
1. Exact match on DOI or arXiv ID
2. Exact match on normalized title
3. Fuzzy title match with author awareness
4. Author-aware deduplication

The service handles:
- Same paper from multiple sources
- Different versions of the same paper
- Papers with similar titles but different authors
- Author name variations (initials, full names)
"""

from __future__ import annotations

import re

from schemas.paper import AuthorDTO, PaperDTO
from utils.normalize import normalize_arxiv_id, normalize_doi, normalize_title

# ── Blocking key helpers ──────────────────────────────────────────────────────


def _blocking_key(title_norm: str) -> str:
    """
    Return a cheap blocking key for a normalised title.

    Papers that share the same first 6 characters are placed in the same
    "block" and compared with fuzzy matching only against each other.
    This reduces the comparison space from O(n²) to roughly O(n * block_size),
    where block_size is typically 1–5 papers.

    6 characters is a pragmatic choice:
    - Short enough to group near-duplicates with minor prefix differences.
    - Long enough to avoid huge blocks on common words like "the " or "a ".
    """
    return title_norm[:6] if len(title_norm) >= 6 else title_norm


# ── Author helpers ────────────────────────────────────────────────────────────


def _normalize_author_name(name: str) -> str:
    """
    Normalize author name for comparison.

    Handles:
    - Case normalization
    - Initial vs full name matching
    - Whitespace normalization
    """
    if not name:
        return ""

    # Lowercase and strip
    normalized = name.lower().strip()

    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove periods from initials (J. Smith -> J Smith)
    normalized = re.sub(r"(\w)\.", r"\1", normalized)

    return normalized


def _author_overlap(authors1: list[AuthorDTO], authors2: list[AuthorDTO]) -> float:
    """
    Calculate author overlap between two papers.

    Returns:
        Float between 0.0 and 1.0 indicating author similarity
    """
    if not authors1 or not authors2:
        return 0.0

    # Normalize author names
    names1 = {_normalize_author_name(a.name) for a in authors1 if a.name}
    names2 = {_normalize_author_name(a.name) for a in authors2 if a.name}

    if not names1 or not names2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = names1 & names2
    union = names1 | names2

    if not union:
        return 0.0

    return len(intersection) / len(union)


def _has_common_author(
    authors1: list[AuthorDTO], authors2: list[AuthorDTO], threshold: float = 0.3
) -> bool:
    """
    Check if two papers share at least one common author.

    Args:
        threshold: Minimum overlap ratio to consider as same author
    """
    return _author_overlap(authors1, authors2) >= threshold


# ── Service ───────────────────────────────────────────────────────────────────


class DedupConfig:
    """Configuration for deduplication behavior."""

    # Title similarity threshold for fuzzy matching
    title_similarity_threshold: float = 92.0

    # Author overlap threshold for author-aware dedup
    author_overlap_threshold: float = 0.3

    # Minimum author overlap to merge papers with same title
    merge_author_threshold: float = 0.2


class DedupService:
    """
    Deduplication pipeline with four tiers:

    1. Exact match on DOI or arXiv ID  — O(1) per paper via dict lookup.
    2. Exact match on normalised title — O(1) per paper via dict lookup.
    3. Fuzzy title match               — O(block_size) per paper via prefix blocking.
    4. Author-aware dedup              — Considers author overlap for similar titles.

    The fuzzy tier only runs for papers that have no DOI/arXiv ID, keeping
    the overall complexity close to O(n) for typical academic datasets.
    """

    def __init__(self, config: DedupConfig | None = None):
        """Initialize dedup service with optional config."""
        self.config = config or DedupConfig()

    def dedupe(self, papers: list[PaperDTO]) -> list[PaperDTO]:
        """
        Deduplicate a list of papers.

        Args:
            papers: List of papers to deduplicate

        Returns:
            Deduplicated list of papers
        """
        from rapidfuzz import fuzz

        # seen: canonical_key → PaperDTO
        seen: dict[str, PaperDTO] = {}

        # blocks: blocking_key → list of canonical keys in that block
        # Used to limit fuzzy comparisons to papers with similar title prefixes.
        blocks: dict[str, list[str]] = {}

        for paper in papers:
            key = DedupService.primary_key(paper)

            # ── Tier 1 & 2: exact key match ───────────────────────────────────
            if key in seen:
                seen[key] = DedupService.merge(seen[key], paper)
                continue

            # ── Tier 3: fuzzy match within the same prefix block ──────────────
            if not (key.startswith("doi:") or key.startswith("arxiv:")):
                title_norm = normalize_title(paper.title)
                bkey = _blocking_key(title_norm)
                candidate_keys = blocks.get(bkey, [])

                merged = False
                for ckey in candidate_keys:
                    existing = seen.get(ckey)
                    if existing is None:
                        continue

                    # Check title similarity
                    title_sim = fuzz.token_set_ratio(title_norm, normalize_title(existing.title))

                    if title_sim > self.config.title_similarity_threshold:
                        # ── Tier 4: Author-aware dedup ──────────────────────
                        # If titles are very similar, check author overlap
                        author_overlap = _author_overlap(paper.authors, existing.authors)

                        # Merge if:
                        # 1. High title similarity (>95) OR
                        # 2. Good title similarity (>90) AND some author overlap
                        if (
                            title_sim > 95
                            or (title_sim > 90 and author_overlap > 0.1)
                            or author_overlap > self.config.author_overlap_threshold
                        ):
                            seen[ckey] = DedupService.merge(existing, paper)
                            merged = True
                            break

                if not merged:
                    seen[key] = paper
                    blocks.setdefault(bkey, []).append(key)
            else:
                # DOI / arXiv — no fuzzy needed, just store
                seen[key] = paper

        return list(seen.values())

    @staticmethod
    def primary_key(paper: PaperDTO) -> str:
        """Generate primary key for a paper."""
        doi = normalize_doi(paper.doi)
        if doi:
            return f"doi:{doi}"
        arxiv_id = normalize_arxiv_id(paper.arxiv_id)
        if arxiv_id:
            return f"arxiv:{arxiv_id}"
        return f"title:{normalize_title(paper.title)}"

    @staticmethod
    def merge(left: PaperDTO, right: PaperDTO) -> PaperDTO:
        """
        Merge two papers into one.

        Takes the best values from both papers:
        - Longer abstract
        - Higher citation count
        - More authors
        - More sources
        """
        data = left.model_dump()
        right_data = right.model_dump()

        # Merge simple fields (take non-empty from right)
        for key, value in right_data.items():
            if key in ("sources", "authors"):
                continue  # Handle separately
            if data.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
                data[key] = value

        # Merge sources (combine both)
        data["sources"] = sorted(set(left.sources + right.sources + [left.source, right.source]))

        # Merge citation count (take max)
        data["citation_count"] = max(left.citation_count or 0, right.citation_count or 0) or None

        # Merge open access (OR)
        data["is_open_access"] = left.is_open_access or right.is_open_access

        # Merge abstract (take longer one)
        if right.abstract and (not left.abstract or len(right.abstract) > len(left.abstract)):
            data["abstract"] = right.abstract

        # Merge authors (combine and deduplicate)
        left_authors = {a.name: a for a in left.authors if a.name}
        right_authors = {a.name: a for a in right.authors if a.name}

        # Merge: prefer right's author info if same name
        merged_authors = dict(left_authors)
        for name, author in right_authors.items():
            if name not in merged_authors:
                merged_authors[name] = author
            else:
                # Prefer non-None fields
                existing = merged_authors[name]
                merged_data = existing.model_dump()
                for field in ("orcid", "affiliation"):
                    if getattr(existing, field) is None and getattr(author, field) is not None:
                        merged_data[field] = getattr(author, field)
                merged_authors[name] = AuthorDTO(**merged_data)

        data["authors"] = list(merged_authors.values())

        return PaperDTO(**data)


# Module-level convenience
_dedup_service: DedupService | None = None


def get_dedup_service() -> DedupService:
    """Get the singleton DedupService instance."""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DedupService()
    return _dedup_service
