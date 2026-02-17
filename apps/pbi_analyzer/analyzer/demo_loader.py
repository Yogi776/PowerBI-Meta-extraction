from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict
from typing import Dict, List

from .models import MeasureDetail, ReportAnalysis, SectionSummary
from .semantic import COMPLEXITY_TOKENS


def _score_ref(name: str) -> tuple[int, List[str]]:
    lowered = name.lower()
    matched = [tok for tok in COMPLEXITY_TOKENS if tok in lowered]
    score = len(matched)
    if lowered.startswith(("sum(", "min(", "max(", "average(", "count(", "distinctcount(")):
        score = max(0, score - 1)
    return score, matched


def load_precomputed_report(report_folder: pathlib.Path) -> ReportAnalysis:
    report_name = report_folder.name
    visual_path = report_folder / "visual_queries.json"
    refs_path = report_folder / "semantic_references.json"

    visual_queries = json.loads(visual_path.read_text(encoding="utf-8")) if visual_path.exists() else []
    semantic_refs = json.loads(refs_path.read_text(encoding="utf-8")) if refs_path.exists() else []

    ref_usage = Counter()
    ref_sections: Dict[str, set] = defaultdict(set)
    section_refs: Dict[str, set] = defaultdict(set)

    for q in visual_queries:
        section = q.get("section", "Unknown")
        projections = q.get("projections", {})
        for _, arr in projections.items():
            if not isinstance(arr, list):
                continue
            for item in arr:
                if isinstance(item, dict) and "queryRef" in item:
                    ref = str(item["queryRef"])
                    ref_usage[ref] += 1
                    ref_sections[ref].add(section)
                    section_refs[section].add(ref)

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

    section_summaries = []
    for section, refs in section_refs.items():
        section_summaries.append(
            SectionSummary(
                section=section,
                unique_refs=len(refs),
                complexity_score=sum(_score_ref(r)[0] for r in refs),
            )
        )
    section_summaries.sort(key=lambda s: (-s.complexity_score, -s.unique_refs, s.section.lower()))

    unique_measure_keys = {
        (r.get("table") or "Unknown", r.get("name") or "Unknown")
        for r in semantic_refs
        if r.get("type") == "Measure"
    }
    unique_column_keys = {
        (r.get("table") or "Unknown", r.get("name") or "Unknown")
        for r in semantic_refs
        if r.get("type") == "Column"
    }

    return ReportAnalysis(
        report_name=report_name,
        source_mode="demo_precomputed",
        total_queries=len(visual_queries),
        total_refs=len(semantic_refs),
        unique_measures=len(unique_measure_keys),
        unique_columns=len(unique_column_keys),
        measures=measures,
        section_summaries=section_summaries,
        visual_queries=visual_queries,
        semantic_references=semantic_refs,
        has_dax_formulas=False,
        has_bim=False,
    )


def load_demo_reports(repo_root: pathlib.Path) -> Dict[str, ReportAnalysis]:
    base = repo_root / "out" / "powerbi-examples-all" / "report-query-logic"
    if not base.exists():
        return {}
    reports: Dict[str, ReportAnalysis] = {}
    for folder in sorted(base.iterdir()):
        if not folder.is_dir():
            continue
        if not (folder / "visual_queries.json").exists():
            continue
        analysis = load_precomputed_report(folder)
        reports[analysis.report_name] = analysis
    return reports
