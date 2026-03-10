from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict
from typing import Any, Dict, List

from .engine import merge_dax_into_analysis
from .models import MeasureDetail, ReportAnalysis, SectionSummary
from .semantic import COMPLEXITY_TOKENS


def _score_ref(name: str) -> tuple[int, List[str]]:
    lowered = name.lower()
    matched = [tok for tok in COMPLEXITY_TOKENS if tok in lowered]
    score = len(matched)
    if lowered.startswith(("sum(", "min(", "max(", "average(", "count(", "distinctcount(")):
        score = max(0, score - 1)
    return score, matched


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


def _load_legacy_dax_measures(legacy_root: pathlib.Path) -> Dict[str, MeasureDetail]:
    measures: Dict[str, MeasureDetail] = {}
    for dax_path in legacy_root.glob("Model/tables/*/measures/*.dax"):
        table_name = dax_path.parents[1].name
        measure_name = dax_path.stem
        full_name = f"{table_name}.{measure_name}"
        try:
            formula = dax_path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            formula = dax_path.read_text(encoding="latin1").strip()

        score, matched = _score_ref(full_name)
        measures[full_name] = MeasureDetail(
            name=full_name,
            source="dax",
            usage_count=0,
            sections=[],
            dax_formula=formula,
            matched_tokens=matched,
            complexity_score=score,
        )
    return measures


def _read_json_if_exists(path: pathlib.Path) -> Any:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _load_legacy_bim(legacy_root: pathlib.Path) -> Dict[str, Any]:
    bim_path = legacy_root.parent / f"{legacy_root.name}.bim"
    bim_json = _read_json_if_exists(bim_path)
    if not isinstance(bim_json, dict):
        return {"bim_path": str(bim_path), "tables": [], "relationships": [], "dictionary": []}

    model = bim_json.get("model", {})
    if not isinstance(model, dict):
        return {"bim_path": str(bim_path), "tables": [], "relationships": [], "dictionary": []}

    tables = []
    dictionary: List[Dict[str, Any]] = []
    for table in model.get("tables", []) if isinstance(model.get("tables", []), list) else []:
        if not isinstance(table, dict):
            continue
        table_name = table.get("name")
        tables.append(
            {
                "name": table_name,
                "isHidden": table.get("isHidden", False),
            }
        )
        dictionary.append(
            {
                "object_type": "Table",
                "table": table_name,
                "name": table_name,
                "data_type": "",
                "hidden": table.get("isHidden", False),
                "description": table.get("description", ""),
                "expression_preview": "",
            }
        )

        columns = table.get("columns", []) if isinstance(table.get("columns", []), list) else []
        for col in columns:
            if not isinstance(col, dict):
                continue
            dictionary.append(
                {
                    "object_type": "Column",
                    "table": table_name,
                    "name": col.get("name"),
                    "data_type": col.get("dataType", ""),
                    "hidden": col.get("isHidden", False),
                    "description": col.get("description", ""),
                    "expression_preview": str(col.get("expression", "")),
                }
            )

        measures = table.get("measures", []) if isinstance(table.get("measures", []), list) else []
        for measure in measures:
            if not isinstance(measure, dict):
                continue
            dictionary.append(
                {
                    "object_type": "Measure",
                    "table": table_name,
                    "name": measure.get("name"),
                    "data_type": "",
                    "hidden": measure.get("isHidden", False),
                    "description": measure.get("description", ""),
                    "expression_preview": str(measure.get("expression", "")),
                }
            )

    relationships = []
    for rel in model.get("relationships", []) if isinstance(model.get("relationships", []), list) else []:
        if not isinstance(rel, dict):
            continue
        relationships.append(
            {
                "name": rel.get("name"),
                "fromTable": rel.get("fromTable"),
                "fromColumn": rel.get("fromColumn"),
                "toTable": rel.get("toTable"),
                "toColumn": rel.get("toColumn"),
                "crossFilteringBehavior": rel.get("crossFilteringBehavior"),
                "toCardinality": rel.get("toCardinality"),
            }
        )

    return {
        "bim_path": str(bim_path),
        "tables": tables,
        "relationships": relationships,
        "dictionary": dictionary,
    }


def _build_model_flow_dot(
    report_name: str, relationships: List[Dict[str, Any]], max_edges: int = 250
) -> str:
    lines = [
        "digraph ModelFlow {",
        "  graph [overlap=false, splines=true];",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fillcolor="#EEF4FF", color="#8BA3CC", fontsize=10];',
        f'  report [shape=oval, fillcolor="#E8FFF2", color="#72B98C", label="{_dot_escape(report_name)}"];',
    ]

    seen_nodes = set()
    edge_count = 0
    for rel in relationships:
        from_table = str(rel.get("fromTable") or "Unknown")
        to_table = str(rel.get("toTable") or "Unknown")
        if from_table not in seen_nodes:
            lines.append(f'  "{_dot_escape(from_table)}";')
            seen_nodes.add(from_table)
            lines.append(f'  report -> "{_dot_escape(from_table)}" [style=dotted, color="#BFD0EA"];')
        if to_table not in seen_nodes:
            lines.append(f'  "{_dot_escape(to_table)}";')
            seen_nodes.add(to_table)
            lines.append(f'  report -> "{_dot_escape(to_table)}" [style=dotted, color="#BFD0EA"];')

        label = f'{rel.get("fromColumn") or ""} -> {rel.get("toColumn") or ""}'.strip()
        lines.append(
            f'  "{_dot_escape(from_table)}" -> "{_dot_escape(to_table)}" '
            f'[label="{_dot_escape(label)}", fontsize=9, color="#6E84A8"];'
        )
        edge_count += 1
        if edge_count >= max_edges:
            break

    if len(relationships) > max_edges:
        lines.append(
            f'  more [shape=note, fillcolor="#FFF7E8", color="#D2B370", '
            f'label="Showing first {max_edges} of {len(relationships)} relationships"];'
        )
    lines.append("}")
    return "\n".join(lines)


def _build_flow_dot(
    report_name: str,
    section_count: int,
    visual_count: int,
    semantic_ref_count: int,
    table_count: int,
    dax_measure_count: int,
    power_query_count: int,
    diagram_node_count: int,
) -> str:
    return "\n".join(
        [
            "digraph LegacyFlow {",
            '  rankdir=LR;',
            '  node [shape=box, style="rounded,filled", fillcolor="#F4F6FA", color="#9AA7BD"];',
            f'  report [label="{report_name}"];',
            f'  report_sections [label="Report Sections ({section_count})"];',
            f'  report_visuals [label="Visual Containers ({visual_count})"];',
            f'  semantic_refs [label="Semantic Refs ({semantic_ref_count})"];',
            f'  model_tables [label="Model Tables ({table_count})"];',
            f'  dax_measures [label="DAX Measures ({dax_measure_count})"];',
            f'  power_queries [label="Power Query .m ({power_query_count})"];',
            f'  diagram_nodes [label="Diagram Nodes ({diagram_node_count})"];',
            '  report -> report_sections -> report_visuals -> semantic_refs;',
            '  report -> model_tables -> dax_measures;',
            '  report -> power_queries;',
            '  report -> diagram_nodes;',
            "}",
        ]
    )


def _estimate_bookmarks_count(report_root: pathlib.Path) -> int:
    # Best effort: count bookmark entries in any bookmark-related JSON files.
    total = 0
    for path in report_root.rglob("*bookmark*.json"):
        payload = _read_json_if_exists(path)
        if isinstance(payload, dict):
            for key in ("bookmarks", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    total += len(value)
                    break
            else:
                # If it is a bookmark-like object but no list key, count as 1.
                total += 1
        elif isinstance(payload, list):
            total += len(payload)
    return total


def _build_report_layout_profile(report_root: pathlib.Path) -> Dict[str, Any]:
    pages_detail: List[Dict[str, Any]] = []
    visual_types_total: Dict[str, int] = defaultdict(int)
    visuals_total = 0
    hidden_pages = 0

    sections_dir = report_root / "sections"
    section_dirs = sorted(p for p in sections_dir.iterdir() if p.is_dir()) if sections_dir.exists() else []
    for section_dir in section_dirs:
        section_json = _read_json_if_exists(section_dir / "section.json")
        section_name = section_dir.name
        hidden = False
        if isinstance(section_json, dict):
            section_name = (
                section_json.get("displayName")
                or section_json.get("name")
                or section_dir.name
            )
            # Best effort: displayOption 1 is normal visible mode in sampled files.
            hidden = section_json.get("displayOption") == 0

        visuals_dir = section_dir / "visualContainers"
        visual_dirs = sorted(p for p in visuals_dir.iterdir() if p.is_dir()) if visuals_dir.exists() else []
        page_types: Dict[str, int] = defaultdict(int)
        page_visuals = 0

        for visual_dir in visual_dirs:
            page_visuals += 1
            visuals_total += 1
            visual_type = "unknown"
            cfg = _read_json_if_exists(visual_dir / "config.json")
            if isinstance(cfg, dict):
                single_visual = cfg.get("singleVisual", {})
                if isinstance(single_visual, dict):
                    visual_type = str(single_visual.get("visualType") or "unknown")
            page_types[visual_type] += 1
            visual_types_total[visual_type] += 1

        if hidden:
            hidden_pages += 1

        pages_detail.append(
            {
                "page": section_name,
                "hidden": hidden,
                "visuals": page_visuals,
                "visual_types": dict(page_types),
            }
        )

    return {
        "present": bool(section_dirs),
        "pages": len(section_dirs),
        "hidden_pages": hidden_pages,
        "visuals_total": visuals_total,
        "visual_types_total": dict(visual_types_total),
        "bookmarks_count_best_effort": _estimate_bookmarks_count(report_root),
        "pages_detail": pages_detail,
    }


def _build_signals_profile(
    legacy_root: pathlib.Path, report_root: pathlib.Path, bim_data: Dict[str, Any]
) -> Dict[str, Any]:
    files = [p for p in legacy_root.rglob("*") if p.is_file()]
    largest = sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:10]
    largest_entries_top10 = [
        {
            "path": str(p.relative_to(legacy_root)),
            "size_bytes": p.stat().st_size,
        }
        for p in largest
    ]

    bim_path = pathlib.Path(str(bim_data.get("bim_path") or ""))
    bim_size = bim_path.stat().st_size if bim_path.exists() and bim_path.is_file() else 0

    return {
        "files_count": len(files),
        "largest_entries_top10": largest_entries_top10,
        "has_report_layout": report_root.exists(),
        "datamodel_present_best_effort": bim_size > 0,
        "datamodel_uncompressed_size_best_effort": bim_size,
    }


def _build_complexity_profile(report_layout: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    pages = int(report_layout.get("pages", 0))
    visuals = int(report_layout.get("visuals_total", 0))
    visual_types = report_layout.get("visual_types_total", {}) or {}
    heavy_visuals = int(
        visual_types.get("pivotTable", 0)
        + visual_types.get("tableEx", 0)
        + visual_types.get("matrix", 0)
        + visual_types.get("barChart", 0)
        + visual_types.get("lineChart", 0)
    )
    datamodel_mb = round(
        float(signals.get("datamodel_uncompressed_size_best_effort", 0)) / (1024 * 1024), 2
    )

    score = min(100.0, pages * 4 + visuals * 0.9 + heavy_visuals * 1.5 + datamodel_mb * 0.2)
    if score >= 75:
        label = "Complex"
    elif score >= 45:
        label = "Moderate"
    else:
        label = "Simple"

    return {
        "score": round(score, 1),
        "label": label,
        "signals": {
            "pages": pages,
            "visuals": visuals,
            "heavy_visuals": heavy_visuals,
            "datamodel_mb_best_effort": datamodel_mb,
        },
    }


def _build_legacy_overview(
    legacy_root: pathlib.Path,
    report_root: pathlib.Path,
    report_name: str,
    visual_queries: List[dict],
    semantic_refs: List[dict],
    dax_measures: Dict[str, MeasureDetail],
) -> Dict[str, Any]:
    report_metadata = _read_json_if_exists(legacy_root / "ReportMetadata.json")
    report_settings = _read_json_if_exists(legacy_root / "ReportSettings.json")
    connections = _read_json_if_exists(legacy_root / "Connections.json")
    diagram_layout = _read_json_if_exists(legacy_root / "DiagramLayout.json")
    bim_data = _load_legacy_bim(legacy_root)

    table_rows: List[Dict[str, Any]] = []
    tables_dir = legacy_root / "Model" / "tables"
    table_dirs = sorted(p for p in tables_dir.iterdir() if p.is_dir()) if tables_dir.exists() else []
    for table_dir in table_dirs:
        measure_dir = table_dir / "measures"
        measure_count = len(list(measure_dir.glob("*.dax"))) if measure_dir.exists() else 0
        json_count = len(list(table_dir.glob("*.json")))
        table_rows.append(
            {
                "table": table_dir.name,
                "measure_count": measure_count,
                "table_json_files": json_count,
            }
        )

    query_rows: List[Dict[str, Any]] = []
    queries_dir = legacy_root / "Model" / "queries"
    query_files = sorted(queries_dir.glob("*.m")) if queries_dir.exists() else []
    for query_file in query_files:
        try:
            body = query_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            body = query_file.read_text(encoding="latin1")
        query_rows.append(
            {
                "query": query_file.stem,
                "line_count": len(body.splitlines()),
            }
        )

    diagram_nodes: List[Dict[str, Any]] = []
    if isinstance(diagram_layout, dict):
        diagrams = diagram_layout.get("diagrams", [])
        if isinstance(diagrams, list):
            for diagram in diagrams:
                nodes = diagram.get("nodes", []) if isinstance(diagram, dict) else []
                if not isinstance(nodes, list):
                    continue
                for node in nodes:
                    if not isinstance(node, dict):
                        continue
                    diagram_nodes.append(
                        {
                            "diagram": diagram.get("name", "Unnamed"),
                            "node": node.get("nodeIndex"),
                            "x": (node.get("location") or {}).get("x"),
                            "y": (node.get("location") or {}).get("y"),
                        }
                    )

    section_count = len({q.get("section", "Unknown") for q in visual_queries})
    visual_count = len(visual_queries)
    semantic_ref_count = len(semantic_refs)
    table_count = len(table_rows)
    dax_measure_count = len(dax_measures)
    power_query_count = len(query_rows)
    diagram_node_count = len(diagram_nodes)
    relationship_count = len(bim_data.get("relationships", []))

    flow_dot = _build_flow_dot(
        report_name=report_name,
        section_count=section_count,
        visual_count=visual_count,
        semantic_ref_count=semantic_ref_count,
        table_count=table_count,
        dax_measure_count=dax_measure_count,
        power_query_count=power_query_count,
        diagram_node_count=diagram_node_count,
    )
    model_flow_dot = _build_model_flow_dot(
        report_name=report_name,
        relationships=bim_data.get("relationships", []),
    )
    report_layout_profile = _build_report_layout_profile(report_root)
    signals_profile = _build_signals_profile(legacy_root, report_root, bim_data)
    complexity_profile = _build_complexity_profile(report_layout_profile, signals_profile)

    return {
        "legacy_root": str(legacy_root),
        "report_root": str(report_root),
        "bim_path": bim_data.get("bim_path"),
        "report_metadata": report_metadata or {},
        "report_settings": report_settings or {},
        "connections": connections or {},
        "counts": {
            "sections": section_count,
            "visual_queries": visual_count,
            "semantic_refs": semantic_ref_count,
            "model_tables": table_count,
            "dax_measures": dax_measure_count,
            "power_queries": power_query_count,
            "diagram_nodes": diagram_node_count,
            "relationships": relationship_count,
        },
        "tables": table_rows,
        "queries": query_rows,
        "diagram_nodes": diagram_nodes,
        "relationships": bim_data.get("relationships", []),
        "bim_tables": bim_data.get("tables", []),
        "data_dictionary": bim_data.get("dictionary", []),
        "report_layout": report_layout_profile,
        "signals": signals_profile,
        "complexity": complexity_profile,
        "flow_dot": flow_dot,
        "model_flow_dot": model_flow_dot,
    }


def load_legacy_report(report_root: pathlib.Path, report_name: str) -> ReportAnalysis:
    visual_queries: List[dict] = []
    semantic_refs: List[dict] = []

    ref_usage = Counter()
    ref_sections: Dict[str, set] = defaultdict(set)
    section_refs: Dict[str, set] = defaultdict(set)

    sections_dir = report_root / "sections"
    section_dirs = sorted(p for p in sections_dir.iterdir() if p.is_dir()) if sections_dir.exists() else []
    for section_dir in section_dirs:
        section_name = section_dir.name
        visuals_dir = section_dir / "visualContainers"
        visual_dirs = sorted(p for p in visuals_dir.iterdir() if p.is_dir()) if visuals_dir.exists() else []

        for visual_dir in visual_dirs:
            config_path = visual_dir / "config.json"
            if not config_path.exists():
                continue
            try:
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
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

            _extract_semantic_refs(query, section_name, semantic_refs)
            visual_queries.append(
                {
                    "section": section_name,
                    "visual": visual_dir.name,
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

    analysis = ReportAnalysis(
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
    legacy_root = report_root.parent
    dax_measures = _load_legacy_dax_measures(legacy_root)
    has_bim = (legacy_root.parent / f"{legacy_root.name}.bim").exists()
    if dax_measures or has_bim:
        analysis = merge_dax_into_analysis(analysis, dax_measures, has_bim=has_bim)
    analysis.legacy_overview = _build_legacy_overview(
        legacy_root=legacy_root,
        report_root=report_root,
        report_name=report_name,
        visual_queries=visual_queries,
        semantic_refs=semantic_refs,
        dax_measures=dax_measures,
    )
    return analysis


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


def load_demo_reports(repo_root: pathlib.Path, project_path: pathlib.Path | None = None) -> Dict[str, ReportAnalysis]:
    data_root = project_path if project_path is not None else (repo_root / "out")
    base = data_root / "powerbi-examples-all" / "report-query-logic"
    reports: Dict[str, ReportAnalysis] = {}

    if base.exists():
        for folder in sorted(base.iterdir()):
            if not folder.is_dir():
                continue
            if not (folder / "visual_queries.json").exists():
                continue
            analysis = load_precomputed_report(folder)
            reports[analysis.report_name] = analysis

    # Also load reports directly from Windows extraction legacy layout.
    # Legacy reports include model relationships/diagram data and can enrich
    # or supersede precomputed entries where names overlap.
    legacy_roots = sorted(data_root.glob("*/windows-extract/legacy/Report"))
    for report_root in legacy_roots:
        report_name = report_root.parents[2].name
        analysis = load_legacy_report(report_root, report_name)
        reports[analysis.report_name] = analysis

    return reports
