from __future__ import annotations

import re
import unicodedata


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip().lower()
    value = (
        value.removeprefix("https://doi.org/").removeprefix("http://doi.org/").removeprefix("doi:")
    )
    return value.strip() or None


def normalize_arxiv_id(arxiv_id: str | None) -> str | None:
    if not arxiv_id:
        return None
    value = arxiv_id.strip().lower()
    value = value.removeprefix("arxiv:")
    value = re.sub(r"v\d+$", "", value)
    return value or None


def normalize_title(title: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value
