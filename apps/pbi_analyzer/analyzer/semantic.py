from __future__ import annotations

import json
import zipfile
from collections import Counter, defaultdict
from io import BytesIO
from typing import Dict, List, Tuple

from .models import MeasureDetail, ReportAnalysis, SectionSummary


COMPLEXITY_TOKENS = [
    "calc",
    "budget",
    "mtd",
    "ytd",
    "qtd",
    "%",
    "index",
    "ly",
    "last year",
    "variance",
    "growth",
    "ratio",
    "margin",
]


def _extract_query_refs_from_projections(projections: dict) -> List[str]:
    refs: List[str] = []
    for _, values in projections.items():
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict) and "queryRef" in item:
                refs.append(str(item["queryRef"]))
    return refs


def _extract_semantic_refs(node, section: str, out_refs: List[dict]) -> None:
    if isinstance(node, dict):
        if "Measure" in node and isinstance(node["Measure"], dict):
            m = node["Measure"]
            out_refs.append(
                {
                    "type": "Measure",
                    "table": m.get("Expression", {}).get("SourceRef", {}).get("Entity"),
                    "name": m.get("Property"),
                    "section": section,
                }
            )
        if "Column" in node and isinstance(node["Column"], dict):
            c = node["Column"]
            out_refs.append(
                {
                    "type": "Column",
                    "table": c.get("Expression", {}).get("SourceRef", {}).get("Entity"),
                    "name": c.get("Property"),
                    "section": section,
                }
            )
        for value in node.values():
            _extract_semantic_refs(value, section, out_refs)
        return

    if isinstance(node, list):
        for value in node:
            _extract_semantic_refs(value, section, out_refs)


def _score_ref(name: str) -> Tuple[int, List[str]]:
    lowered = name.lower()
    matched = [tok for tok in COMPLEXITY_TOKENS if tok in lowered]
    score = len(matched)
    if lowered.startswith(("sum(", "min(", "max(", "average(", "count(", "distinctcount(")):
        score = max(0, score - 1)
    return score, matched


def analyze_pbix_bytes(pbix_name: str, pbix_content: bytes) -> ReportAnalysis:
    with zipfile.ZipFile(BytesIO(pbix_content), "r") as zf:
        if "Report/Layout" not in zf.namelist():
            raise ValueError("PBIX does not contain Report/Layout. Cannot run semantic analysis.")
        layout_bytes = zf.read("Report/Layout")

    try:
        layout = json.loads(layout_bytes.decode("utf-16-le"))
    except UnicodeDecodeError:
        layout = json.loads(layout_bytes.decode("utf-8"))

    visual_queries: List[dict] = []
    semantic_references: List[dict] = []
    ref_usage = Counter()
    ref_sections: Dict[str, set] = defaultdict(set)
    section_refs: Dict[str, set] = defaultdict(set)

    for section in layout.get("sections", []):
        section_name = section.get("displayName") or section.get("name") or "Unknown"
        for vc in section.get("visualContainers", []):
            config = vc.get("config")
            if not config:
                continue
            try:
                cfg = json.loads(config)
            except json.JSONDecodeError:
                continue
            single_visual = cfg.get("singleVisual", {})
            query = single_visual.get("prototypeQuery") or single_visual.get("query")
            if not query:
                continue

            projections = single_visual.get("projections", {})
            query_refs = _extract_query_refs_from_projections(projections)
            for ref in query_refs:
                ref_usage[ref] += 1
                ref_sections[ref].add(section_name)
                section_refs[section_name].add(ref)

            _extract_semantic_refs(query, section_name, semantic_references)
            visual_queries.append(
                {
                    "section": section_name,
                    "x": vc.get("x"),
                    "y": vc.get("y"),
                    "width": vc.get("width"),
                    "height": vc.get("height"),
                    "projections": projections,
                    "query": query,
                }
            )

    measures: Dict[str, MeasureDetail] = {}
    for ref, count in ref_usage.items():
        score, matched = _score_ref(ref)
        measures[ref] = MeasureDetail(
            name=ref,
            source="query_ref",
            usage_count=count,
            sections=sorted(ref_sections[ref]),
            matched_tokens=matched,
            complexity_score=score,
        )

    section_summaries: List[SectionSummary] = []
    for sec, refs in section_refs.items():
        sec_score = sum(_score_ref(r)[0] for r in refs)
        section_summaries.append(
            SectionSummary(section=sec, unique_refs=len(refs), complexity_score=sec_score)
        )
    section_summaries.sort(key=lambda s: (-s.complexity_score, -s.unique_refs, s.section.lower()))

    unique_measure_keys = {
        (r.get("table") or "Unknown", r.get("name") or "Unknown")
        for r in semantic_references
        if r.get("type") == "Measure"
    }
    unique_column_keys = {
        (r.get("table") or "Unknown", r.get("name") or "Unknown")
        for r in semantic_references
        if r.get("type") == "Column"
    }

    return ReportAnalysis(
        report_name=pbix_name,
        source_mode="semantic_only",
        total_queries=len(visual_queries),
        total_refs=len(semantic_references),
        unique_measures=len(unique_measure_keys),
        unique_columns=len(unique_column_keys),
        measures=measures,
        section_summaries=section_summaries,
        visual_queries=visual_queries,
        semantic_references=semantic_references,
        has_dax_formulas=False,
        has_bim=False,
    )
