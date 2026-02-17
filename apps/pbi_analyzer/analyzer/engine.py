from __future__ import annotations

import pathlib
from typing import Dict

from .models import MeasureDetail, ReportAnalysis


def _normalize_for_match(value: str) -> str:
    return (
        value.lower()
        .replace("sum(", "")
        .replace(")", "")
        .replace("[", ".")
        .replace("]", "")
        .replace("/", ".")
        .replace("_", "")
        .replace(" ", "")
    )


def _variants(value: str) -> set[str]:
    base = value.lower()
    variants = {
        base,
        base.replace("sum(", "").replace(")", ""),
        base.replace("[", ".").replace("]", ""),
        base.replace("/", "."),
        base.replace("_", ""),
        base.replace(" ", ""),
    }
    combined = set()
    for v in variants:
        combined.add(v)
        combined.add(
            v.replace("sum(", "")
            .replace(")", "")
            .replace("[", ".")
            .replace("]", "")
            .replace("/", ".")
            .replace("_", "")
            .replace(" ", "")
        )
    return {x for x in combined if x}


def merge_dax_into_analysis(
    analysis: ReportAnalysis, dax_measures: Dict[str, MeasureDetail], has_bim: bool
) -> ReportAnalysis:
    if not dax_measures:
        analysis.has_bim = has_bim
        return analysis

    # Keep existing semantic rows, enrich when possible.
    semantic_items = list(analysis.measures.items())
    dax_lookup: Dict[str, MeasureDetail] = {}
    for name, detail in dax_measures.items():
        for v in _variants(name):
            dax_lookup[v] = detail
    used_dax_keys = set()

    for key, measure in semantic_items:
        matched = None
        for candidate in _variants(key):
            if candidate in dax_lookup:
                matched = candidate
                break
        if matched is not None:
            dax_detail = dax_lookup[matched]
            measure.source = "dax"
            measure.dax_formula = dax_detail.dax_formula
            used_dax_keys.add(matched)

    # Add unmatched dax measures so user sees complete formulas present in artifacts.
    for norm_key, dax_detail in dax_lookup.items():
        if norm_key in used_dax_keys:
            continue
        if dax_detail.name in analysis.measures:
            continue
        analysis.measures[dax_detail.name] = dax_detail

    analysis.has_dax_formulas = True
    analysis.has_bim = has_bim
    analysis.source_mode = "dax_enriched"
    return analysis


def build_markdown_summary(analysis: ReportAnalysis) -> str:
    lines = [
        f"# PowerBI Analysis Summary - {analysis.report_name}",
        "",
        f"- Source mode: `{analysis.source_mode}`",
        f"- Visual queries: {analysis.total_queries}",
        f"- Semantic references: {analysis.total_refs}",
        f"- Unique measures: {analysis.unique_measures}",
        f"- Unique columns: {analysis.unique_columns}",
        f"- DAX formulas available: {analysis.has_dax_formulas}",
        f"- BIM file available: {analysis.has_bim}",
        "",
        "## Top Measure Logic Candidates",
    ]

    for m in analysis.top_measures(25):
        suffix = " (formula available)" if m.dax_formula else " (query-ref only)"
        lines.append(
            f"- `{m.name}` | score={m.complexity_score} | usage={m.usage_count}{suffix}"
        )

    lines.extend(["", "## Section Logic Density"])
    for sec in analysis.section_summaries[:20]:
        lines.append(
            f"- `{sec.section}` | complexity_score={sec.complexity_score} | unique_refs={sec.unique_refs}"
        )
    return "\n".join(lines)


def repo_root_from_app() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]
