from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MeasureDetail:
    name: str
    source: str  # dax | query_ref
    usage_count: int = 0
    sections: List[str] = field(default_factory=list)
    dax_formula: str = ""
    matched_tokens: List[str] = field(default_factory=list)
    complexity_score: int = 0


@dataclass
class SectionSummary:
    section: str
    unique_refs: int
    complexity_score: int


@dataclass
class ReportAnalysis:
    report_name: str
    source_mode: str  # semantic_only | dax_enriched | demo_precomputed
    total_queries: int = 0
    total_refs: int = 0
    unique_measures: int = 0
    unique_columns: int = 0
    measures: Dict[str, MeasureDetail] = field(default_factory=dict)
    section_summaries: List[SectionSummary] = field(default_factory=list)
    visual_queries: List[dict] = field(default_factory=list)
    semantic_references: List[dict] = field(default_factory=list)
    has_dax_formulas: bool = False
    has_bim: bool = False

    def top_measures(self, limit: int = 25) -> List[MeasureDetail]:
        ranked = sorted(
            self.measures.values(),
            key=lambda m: (-m.complexity_score, -m.usage_count, m.name.lower()),
        )
        return ranked[:limit]
