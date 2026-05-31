from __future__ import annotations

import csv
import io
import json
from typing import Any

from schemas.paper import PaperDTO


def _bibtex_key(paper: PaperDTO) -> str:
    first_author = paper.authors[0].name.split()[-1] if paper.authors else "Unknown"
    year = paper.year or "n.d."
    return f"{first_author}{year}".lower()


def _bibtex_authors(paper: PaperDTO) -> str:
    parts = []
    for a in paper.authors:
        names = a.name.split()
        if len(names) > 1:
            parts.append(f"{names[-1]}, {' '.join(names[:-1])}")
        else:
            parts.append(a.name)
    return " and ".join(parts)


def export_bibtex(papers: list[PaperDTO]) -> str:
    lines: list[str] = []
    for paper in papers:
        key = _bibtex_key(paper)
        entry = [f"@article{{{key},"]
        entry.append(f"  title = {{{paper.title}}},")
        entry.append(f"  author = {{{_bibtex_authors(paper)}}},")
        if paper.venue:
            entry.append(f"  journal = {{{paper.venue}}},")
        if paper.year:
            entry.append(f"  year = {{{paper.year}}},")
        if paper.doi:
            entry.append(f"  doi = {{{paper.doi}}},")
        if paper.oa_url:
            entry.append(f"  url = {{{paper.oa_url}}},")
        if paper.abstract:
            entry.append(f"  abstract = {{{paper.abstract}}},")
        entry.append("}")
        lines.append("\n".join(entry))
    return "\n\n".join(lines)


def export_csv(papers: list[PaperDTO]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "title",
            "authors",
            "year",
            "venue",
            "doi",
            "citation_count",
            "is_open_access",
            "abstract",
            "topics",
            "source",
            "landing_url",
            "oa_url",
        ]
    )
    for paper in papers:
        writer.writerow(
            [
                paper.title,
                "; ".join(a.name for a in paper.authors),
                paper.year,
                paper.venue,
                paper.doi,
                paper.citation_count,
                paper.is_open_access,
                paper.abstract,
                ", ".join(paper.topics),
                ", ".join(paper.sources),
                paper.landing_url,
                paper.oa_url,
            ]
        )
    return output.getvalue()


def export_json(papers: list[PaperDTO]) -> str:
    data: list[dict[str, Any]] = []
    for paper in papers:
        d = paper.model_dump(mode="json")
        data.append(d)
    return json.dumps(data, indent=2, ensure_ascii=False)
