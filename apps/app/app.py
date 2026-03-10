from __future__ import annotations

import difflib
import json
import os
import pathlib
from io import BytesIO
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from analyzer.artifacts import ArtifactParseResult, parse_artifact_folder, parse_artifact_zip
from analyzer.demo_loader import load_demo_reports
from analyzer.engine import build_markdown_summary, merge_dax_into_analysis, repo_root_from_app
from analyzer.models import ReportAnalysis
from analyzer.semantic import analyze_pbix_bytes


st.set_page_config(page_title="PowerBI Analyzer Demo", layout="wide")


def _read_project_path_override(repo_root: pathlib.Path) -> pathlib.Path:
    def _resolve_candidate(raw_value: str) -> pathlib.Path:
        p = pathlib.Path(raw_value.strip())
        return p if p.is_absolute() else (repo_root / p)

    # Priority 1: explicit env var
    env_value = os.getenv("project_path") or os.getenv("PROJECT_PATH")
    if env_value:
        candidate = _resolve_candidate(env_value)
        if candidate.exists():
            return candidate

    # Priority 2: local .env file next to app.py
    env_file = pathlib.Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip().lower() != "project_path":
                continue
            candidate = _resolve_candidate(value)
            if candidate.exists():
                return candidate

    # Priority 3: conventional output roots
    repo_out = repo_root / "out"
    if repo_out.exists():
        return repo_out
    app_out = pathlib.Path(__file__).resolve().parent / "out"
    if app_out.exists():
        return app_out
    return repo_out


def _build_download_payload(analysis: ReportAnalysis) -> Dict[str, Any]:
    legacy = analysis.legacy_overview or {}
    report_layout = legacy.get("report_layout") or {}
    complexity = legacy.get("complexity") or {}

    measure_rows = _build_measure_table(analysis)
    measure_rows_clean = []
    if not measure_rows.empty:
        for _, row in measure_rows.iterrows():
            item = row.to_dict()
            item.pop("_Representative", None)
            measure_rows_clean.append(item)

    payload = {
        "report_overview": {
            "report_name": analysis.report_name,
            "source_mode": analysis.source_mode,
            "has_dax_formulas": analysis.has_dax_formulas,
            "has_bim": analysis.has_bim,
            "total_queries": analysis.total_queries,
            "total_refs": analysis.total_refs,
            "unique_measures": analysis.unique_measures,
            "unique_columns": analysis.unique_columns,
        },
        "executive_summary": {
            "section_summaries": [
                {
                    "section": s.section,
                    "unique_refs": s.unique_refs,
                    "complexity_score": s.complexity_score,
                }
                for s in analysis.section_summaries
            ],
            "report_profile": {
                "pages": report_layout.get("pages", 0),
                "hidden_pages": report_layout.get("hidden_pages", 0),
                "visuals_total": report_layout.get("visuals_total", 0),
                "bookmarks_count_best_effort": report_layout.get("bookmarks_count_best_effort", 0),
                "visual_types_total": report_layout.get("visual_types_total", {}),
                "pages_detail": report_layout.get("pages_detail", []),
            },
            "complexity": complexity,
        },
        "measure_logic": {
            "measure_table_deduped": measure_rows_clean,
            "measure_details_full": [
                {
                    "name": m.name,
                    "source": m.source,
                    "usage_count": m.usage_count,
                    "sections": m.sections,
                    "complexity_score": m.complexity_score,
                    "matched_tokens": m.matched_tokens,
                    "dax_formula": m.dax_formula,
                }
                for m in analysis.measures.values()
            ],
        },
        "data_model_analysis": {
            "counts": legacy.get("counts", {}),
            "model_tables": legacy.get("tables", []),
            "model_relationships": legacy.get("relationships", []),
            "data_dictionary": legacy.get("data_dictionary", []),
            "flow_dot": legacy.get("flow_dot", ""),
            "model_flow_dot": legacy.get("model_flow_dot", ""),
        },
    }
    return payload


def _analysis_to_json(analysis: ReportAnalysis) -> str:
    return json.dumps(_build_download_payload(analysis), indent=2)


def _analysis_to_excel_bytes(analysis: ReportAnalysis) -> bytes:
    payload = _build_download_payload(analysis)
    overview = payload["report_overview"]
    exec_summary = payload["executive_summary"]
    measure_logic = payload["measure_logic"]
    model_analysis = payload["data_model_analysis"]

    overview_df = pd.DataFrame(
        [
            {"Metric": "report_name", "Value": overview["report_name"]},
            {"Metric": "source_mode", "Value": overview["source_mode"]},
            {"Metric": "total_queries", "Value": overview["total_queries"]},
            {"Metric": "total_refs", "Value": overview["total_refs"]},
            {"Metric": "unique_measures", "Value": overview["unique_measures"]},
            {"Metric": "unique_columns", "Value": overview["unique_columns"]},
            {"Metric": "has_dax_formulas", "Value": overview["has_dax_formulas"]},
            {"Metric": "has_bim", "Value": overview["has_bim"]},
        ]
    )
    sections_df = pd.DataFrame(
        exec_summary.get("section_summaries", [])
    )
    complexity_df = pd.DataFrame(
        [{"Metric": k, "Value": v} for k, v in (exec_summary.get("complexity") or {}).items() if k != "signals"]
    )
    complexity_signals_df = pd.DataFrame(
        [{"Metric": k, "Value": v} for k, v in ((exec_summary.get("complexity") or {}).get("signals") or {}).items()]
    )
    report_profile_df = pd.DataFrame(
        [{"Metric": k, "Value": v} for k, v in (exec_summary.get("report_profile") or {}).items() if k not in ("visual_types_total", "pages_detail")]
    )
    visual_types_df = pd.DataFrame(
        [{"Visual Type": k, "Count": v} for k, v in ((exec_summary.get("report_profile") or {}).get("visual_types_total") or {}).items()]
    )
    pages_detail_df = pd.DataFrame((exec_summary.get("report_profile") or {}).get("pages_detail") or [])

    measures_dedup_df = pd.DataFrame(measure_logic.get("measure_table_deduped") or [])
    measures_full_df = pd.DataFrame(measure_logic.get("measure_details_full") or [])
    relationships_df = pd.DataFrame(model_analysis.get("model_relationships") or [])
    model_tables_df = pd.DataFrame(model_analysis.get("model_tables") or [])
    dictionary_df = pd.DataFrame(model_analysis.get("data_dictionary") or [])
    counts_df = pd.DataFrame(
        [{"Metric": k, "Value": v} for k, v in (model_analysis.get("counts") or {}).items()]
    )

    output = BytesIO()
    with pd.ExcelWriter(output) as writer:
        overview_df.to_excel(writer, index=False, sheet_name="Overview")
        report_profile_df.to_excel(writer, index=False, sheet_name="ReportProfile")
        visual_types_df.to_excel(writer, index=False, sheet_name="VisualTypes")
        pages_detail_df.to_excel(writer, index=False, sheet_name="PagesDetail")
        sections_df.to_excel(writer, index=False, sheet_name="SectionSummary")
        complexity_df.to_excel(writer, index=False, sheet_name="Complexity")
        complexity_signals_df.to_excel(writer, index=False, sheet_name="ComplexitySignals")
        measures_dedup_df.to_excel(writer, index=False, sheet_name="MeasuresDeduped")
        measures_full_df.to_excel(writer, index=False, sheet_name="MeasureDetails")
        counts_df.to_excel(writer, index=False, sheet_name="ModelCounts")
        model_tables_df.to_excel(writer, index=False, sheet_name="ModelTables")
        relationships_df.to_excel(writer, index=False, sheet_name="Relationships")
        dictionary_df.to_excel(writer, index=False, sheet_name="DataDictionary")
    return output.getvalue()


def _build_measure_table(analysis: ReportAnalysis) -> pd.DataFrame:
    grouped: Dict[str, dict] = {}
    for m in analysis.top_measures(200):
        canonical = (
            m.name.lower()
            .replace("sum(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
        )
        if canonical not in grouped:
            grouped[canonical] = {
                "Measure": m.name,
                "Source": m.source,
                "Complexity": m.complexity_score,
                "Usage Count": m.usage_count,
                "Sections": set(m.sections),
                "Has Formula": bool(m.dax_formula),
                "_Representative": m.name,
            }
            continue

        row = grouped[canonical]
        row["Complexity"] = max(int(row["Complexity"]), int(m.complexity_score))
        row["Usage Count"] = int(row["Usage Count"]) + int(m.usage_count)
        row["Sections"].update(m.sections)
        if bool(m.dax_formula):
            row["Has Formula"] = True
            row["_Representative"] = m.name
        if row["Source"] != m.source:
            row["Source"] = "mixed"

    rows = []
    for row in grouped.values():
        rows.append(
            {
                "Measure": row["Measure"],
                "Source": row["Source"],
                "Complexity": row["Complexity"],
                "Usage Count": row["Usage Count"],
                "Sections": ", ".join(sorted(row["Sections"])),
                "Has Formula": row["Has Formula"],
                "_Representative": row["_Representative"],
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["Has Formula", "Complexity", "Usage Count", "Measure"], ascending=[False, False, False, True])
    return df


def _measure_label(analysis: ReportAnalysis, measure_name: str) -> str:
    detail = analysis.measures[measure_name]
    tag = "[DAX]" if detail.dax_formula else "[REF]"
    return f"{tag} {measure_name}"


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _is_local_date_table(name: str) -> bool:
    return str(name).startswith("LocalDateTable_")


def _exclude_hidden_nodes_relationships(relationships: list[dict]) -> list[dict]:
    filtered = []
    for rel in relationships:
        from_table = str(rel.get("fromTable") or "")
        to_table = str(rel.get("toTable") or "")
        # Hide Power BI auto date tables from flow visuals.
        if _is_local_date_table(from_table) or _is_local_date_table(to_table):
            continue
        filtered.append(rel)
    return filtered


def _relationship_matches(rel: dict, search_text: str) -> bool:
    if not search_text:
        return True
    token = search_text.lower()
    haystack = " | ".join(
        [
            str(rel.get("name") or ""),
            str(rel.get("fromTable") or ""),
            str(rel.get("fromColumn") or ""),
            str(rel.get("toTable") or ""),
            str(rel.get("toColumn") or ""),
            str(rel.get("crossFilteringBehavior") or ""),
            str(rel.get("toCardinality") or ""),
        ]
    ).lower()
    return token in haystack


def _relationship_candidates(relationships: list[dict]) -> list[str]:
    candidates = set()
    for rel in relationships:
        for key in (
            "name",
            "fromTable",
            "fromColumn",
            "toTable",
            "toColumn",
            "crossFilteringBehavior",
            "toCardinality",
        ):
            value = str(rel.get(key) or "").strip()
            if value:
                candidates.add(value)
    return sorted(candidates)


def _render_search_suggestions(search_text: str, relationships: list[dict], label: str) -> None:
    token = (search_text or "").strip()
    if len(token) < 2:
        return
    candidates = _relationship_candidates(relationships)
    close = difflib.get_close_matches(token, candidates, n=6, cutoff=0.35)
    partial = [c for c in candidates if token.lower() in c.lower()][:6]
    suggestions = []
    seen = set()
    for item in close + partial:
        if item in seen:
            continue
        seen.add(item)
        suggestions.append(item)
        if len(suggestions) >= 6:
            break
    if suggestions:
        st.caption(f"{label}: " + ", ".join(f"`{s}`" for s in suggestions))


def _build_model_flow_dot(report_name: str, relationships: list[dict], max_edges: int) -> str:
    lines = [
        "digraph ModelFlow {",
        "  graph [overlap=false, splines=true];",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fillcolor="#EEF4FF", color="#8BA3CC", fontsize=10];',
        f'  report [shape=oval, fillcolor="#E8FFF2", color="#72B98C", label="{_dot_escape(report_name)}"];',
    ]

    seen_nodes = set()
    for idx, rel in enumerate(relationships):
        if idx >= max_edges:
            break
        from_table = str(rel.get("fromTable") or "Unknown")
        to_table = str(rel.get("toTable") or "Unknown")
        from_node = _dot_escape(from_table)
        to_node = _dot_escape(to_table)

        if from_table not in seen_nodes:
            lines.append(f'  "{from_node}";')
            lines.append(f'  report -> "{from_node}" [style=dotted, color="#BFD0EA"];')
            seen_nodes.add(from_table)
        if to_table not in seen_nodes:
            lines.append(f'  "{to_node}";')
            lines.append(f'  report -> "{to_node}" [style=dotted, color="#BFD0EA"];')
            seen_nodes.add(to_table)

        edge_label = f'{rel.get("fromColumn") or ""} -> {rel.get("toColumn") or ""}'.strip()
        lines.append(
            f'  "{from_node}" -> "{to_node}" '
            f'[label="{_dot_escape(edge_label)}", fontsize=9, color="#6E84A8"];'
        )

    if len(relationships) > max_edges:
        lines.append(
            f'  more [shape=note, fillcolor="#FFF7E8", color="#D2B370", '
            f'label="Showing first {max_edges} of {len(relationships)} filtered relationships"];'
        )
    lines.append("}")
    return "\n".join(lines)


def _render_legacy_analysis(analysis: ReportAnalysis) -> None:
    legacy = analysis.legacy_overview or {}
    if not legacy:
        st.info("Legacy deep analysis is available for reports loaded from legacy extraction output.")
        return

    st.subheader("Data Model Analysis")
    counts = legacy.get("counts") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Model Tables", counts.get("model_tables", 0))
    c2.metric("DAX Measures", counts.get("dax_measures", 0))
    c3.metric("Power Queries", counts.get("power_queries", 0))
    c4.metric("Diagram Nodes", counts.get("diagram_nodes", 0))
    st.metric("Relationships", counts.get("relationships", 0))

    report_layout = legacy.get("report_layout") or {}
    complexity = legacy.get("complexity") or {}
    complexity_signals = complexity.get("signals") or {}
    signals = legacy.get("signals") or {}

    st.subheader("Report Profile")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Pages", report_layout.get("pages", 0))
    p2.metric("Hidden Pages", report_layout.get("hidden_pages", 0))
    p3.metric("Visuals Total", report_layout.get("visuals_total", 0))
    p4.metric("Bookmarks (best effort)", report_layout.get("bookmarks_count_best_effort", 0))

    cpx1, cpx2, cpx3, cpx4 = st.columns(4)
    cpx1.metric("Complexity Score", complexity.get("score", 0))
    cpx2.metric("Complexity Label", complexity.get("label", "N/A"))
    cpx3.metric("Heavy Visuals", complexity_signals.get("heavy_visuals", 0))
    cpx4.metric("DataModel MB (best effort)", complexity_signals.get("datamodel_mb_best_effort", 0))

    st.subheader("Visual Types")
    visual_types_total = report_layout.get("visual_types_total") or {}
    total_visuals = int(report_layout.get("visuals_total", 0)) or 1
    visual_types_rows = []
    for k, v in sorted(visual_types_total.items(), key=lambda x: (-x[1], x[0])):
        visual_types_rows.append(
            {
                "Visual Type": k,
                "Count": int(v),
                "Percent": f"{(int(v) / total_visuals) * 100:.1f}%",
            }
        )
    left_col, mid_col, right_col = st.columns([1, 2, 1])
    with mid_col:
        st.dataframe(pd.DataFrame(visual_types_rows), hide_index=True, use_container_width=True)

    st.subheader("Pages Detail")
    st.dataframe(pd.DataFrame(report_layout.get("pages_detail") or []), use_container_width=True)

    with st.expander("Flow diagram", expanded=True):
        dot = legacy.get("flow_dot", "")
        if dot:
            try:
                st.graphviz_chart(dot)
            except Exception as exc:
                st.warning(f"Flow diagram render failed: {exc}")
                st.code(dot, language="dot")
        else:
            st.info("No flow diagram available.")

    with st.expander("Model relationship flow diagram", expanded=True):
        relationships = legacy.get("relationships") or []
        relationships = _exclude_hidden_nodes_relationships(relationships)
        rel_search = st.text_input(
            "Search relationships (table, column, or relationship name)",
            value="",
            key=f"rel_search_{analysis.report_name}",
        )
        _render_search_suggestions(rel_search, relationships, "Similar matches")
        rel_filtered = [r for r in relationships if _relationship_matches(r, rel_search)]
        fullscreen_mode = st.checkbox(
            "Fullscreen diagram mode (large view)",
            value=False,
            key=f"rel_fullscreen_{analysis.report_name}",
        )
        max_edges = st.slider(
            "Max edges in diagram",
            min_value=20,
            max_value=500,
            value=350 if fullscreen_mode else 180,
            key=f"rel_max_edges_{analysis.report_name}",
        )
        st.caption(
            f"Relationships shown after search: {len(rel_filtered)} "
            "(LocalDateTable_* nodes removed)"
        )

        dot = _build_model_flow_dot(analysis.report_name, rel_filtered, max_edges=max_edges)
        if dot and rel_filtered:
            if fullscreen_mode:
                st.markdown(
                    """
<style>
div[data-testid="stGraphVizChart"] svg {
    min-height: 78vh;
}
</style>
""",
                    unsafe_allow_html=True,
                )
            try:
                st.graphviz_chart(dot, use_container_width=True)
            except Exception as exc:
                st.warning(f"Model relationship diagram render failed: {exc}")
                st.code(dot, language="dot")
        else:
            st.info("No model relationship flow diagram available for the current search.")

    st.subheader("Model Tables")
    st.dataframe(pd.DataFrame(legacy.get("tables") or []), use_container_width=True)

    st.subheader("Model Relationships")
    rel_table_search = st.text_input(
        "Search model relationships table",
        value="",
        key=f"rel_table_search_{analysis.report_name}",
    )
    rel_table_rows = legacy.get("relationships") or []
    _render_search_suggestions(rel_table_search, rel_table_rows, "Table search suggestions")
    rel_table_filtered = [r for r in rel_table_rows if _relationship_matches(r, rel_table_search)]
    st.caption(f"Rows shown: {len(rel_table_filtered)} / {len(rel_table_rows)}")
    st.dataframe(pd.DataFrame(rel_table_filtered), use_container_width=True)

    st.subheader("Data Dictionary (from legacy.bim)")
    dd_rows = legacy.get("data_dictionary") or []
    dd_search = st.text_input(
        "Search data dictionary (table, name, type, description)",
        value="",
        key=f"dd_search_{analysis.report_name}",
    )
    dd_types_all = sorted({str(r.get("object_type") or "") for r in dd_rows if r.get("object_type")})
    dd_types = st.multiselect(
        "Filter object types",
        options=dd_types_all,
        default=dd_types_all,
        key=f"dd_type_filter_{analysis.report_name}",
    )
    dd_token = dd_search.lower().strip()
    dd_filtered = []
    for row in dd_rows:
        row_type = str(row.get("object_type") or "")
        if dd_types and row_type not in dd_types:
            continue
        haystack = " | ".join(
            [
                str(row.get("object_type") or ""),
                str(row.get("table") or ""),
                str(row.get("name") or ""),
                str(row.get("data_type") or ""),
                str(row.get("description") or ""),
                str(row.get("expression_preview") or ""),
            ]
        ).lower()
        if dd_token and dd_token not in haystack:
            continue
        dd_filtered.append(row)
    st.caption(f"Dictionary rows shown: {len(dd_filtered)} / {len(dd_rows)}")
    st.dataframe(pd.DataFrame(dd_filtered), use_container_width=True)

    if dd_filtered:
        st.subheader("Expression Viewer")
        dd_options = [
            f"{r.get('object_type', '')} | {r.get('table', '')}.{r.get('name', '')}"
            for r in dd_filtered
        ]
        selected_dd = st.selectbox(
            "Select dictionary object",
            options=dd_options,
            key=f"dd_select_{analysis.report_name}",
        )
        selected_idx = dd_options.index(selected_dd)
        selected_row = dd_filtered[selected_idx]
        expr_full = str(selected_row.get("expression_preview") or "")
        st.write(
            f"**Selected:** `{selected_row.get('object_type', '')}` "
            f"`{selected_row.get('table', '')}.{selected_row.get('name', '')}`"
        )
        if expr_full:
            st.code(expr_full, language="sql")
        else:
            st.info("No expression available for this object.")


def _render_executive_analytics_summary(analysis: ReportAnalysis) -> None:
    legacy = analysis.legacy_overview or {}
    if not legacy:
        st.info("Extended analytics summary is available for reports loaded from legacy extraction output.")
        return

    report_layout = legacy.get("report_layout") or {}
    complexity = legacy.get("complexity") or {}
    complexity_signals = complexity.get("signals") or {}
    counts = legacy.get("counts") or {}

    st.subheader("Analytics Summary")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Pages", report_layout.get("pages", 0))
    a2.metric("Hidden Pages", report_layout.get("hidden_pages", 0))
    a3.metric("Visuals Total", report_layout.get("visuals_total", 0))
    a4.metric("Bookmarks", report_layout.get("bookmarks_count_best_effort", 0))

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Complexity Score", complexity.get("score", 0))
    b2.metric("Complexity Label", complexity.get("label", "N/A"))
    b3.metric("Heavy Visuals", complexity_signals.get("heavy_visuals", 0))
    b4.metric("DataModel MB", complexity_signals.get("datamodel_mb_best_effort", 0))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Model Tables", counts.get("model_tables", 0))
    c2.metric("DAX Measures", counts.get("dax_measures", 0))
    c3.metric("Relationships", counts.get("relationships", 0))
    c4.metric("Dictionary Rows", len(legacy.get("data_dictionary") or []))

    st.markdown("**Visual Types**")
    visual_types_total = report_layout.get("visual_types_total") or {}
    total_visuals = int(report_layout.get("visuals_total", 0)) or 1
    visual_types_rows = [
        {
            "Visual Type": k,
            "Count": int(v),
            "Percent": f"{(int(v) / total_visuals) * 100:.1f}%",
        }
        for k, v in sorted(visual_types_total.items(), key=lambda x: (-x[1], x[0]))
    ]
    st.dataframe(pd.DataFrame(visual_types_rows), hide_index=True, use_container_width=True)

    st.markdown("**Pages Detail**")
    st.dataframe(pd.DataFrame(report_layout.get("pages_detail") or []), use_container_width=True)


def _render_upload_help() -> None:
    st.info(
        "For full DAX formulas, provide extraction artifacts containing `.dax` files "
        "(for example from `.github/workflows/extract-pbix-model.yml`). "
        "Without artifacts, app uses semantic query refs from `Report/Layout`."
    )


def _render_artifact_validation(result: ArtifactParseResult) -> None:
    st.caption(
        f"Artifact scan: dax_files={result.dax_count}, has_bim={result.has_bim}, "
        f"bim_location={result.bim_location}"
    )
    if result.dax_count == 0:
        st.warning(
            "No `.dax` files found. Ensure you loaded extraction artifacts (for example "
            "`pbix-extract-artifacts` from the Windows workflow)."
        )
    if not result.has_bim:
        st.warning("No `.bim` detected in artifact content or expected sibling path.")


def _maybe_enrich_with_artifacts(base: ReportAnalysis, zip_file, folder_text: str) -> ReportAnalysis:
    enriched = base
    if zip_file is not None:
        parsed = parse_artifact_zip(zip_file.getvalue())
        _render_artifact_validation(parsed)
        enriched = merge_dax_into_analysis(enriched, parsed.measures, parsed.has_bim)
    elif folder_text.strip():
        path = pathlib.Path(folder_text.strip())
        if path.exists() and path.is_dir():
            parsed = parse_artifact_folder(str(path))
            _render_artifact_validation(parsed)
            enriched = merge_dax_into_analysis(enriched, parsed.measures, parsed.has_bim)
        else:
            st.warning("Artifact folder path not found. Continuing with semantic-only analysis.")
    return enriched


def main() -> None:
    st.title("PowerBI Analyzer Demo")
    st.caption("Upload PBIX, review logic summaries, and enrich with DAX artifacts when available.")

    root = repo_root_from_app()
    project_data_root = _read_project_path_override(root)
    demo_reports: Dict[str, ReportAnalysis] = load_demo_reports(root, project_data_root)

    with st.sidebar:
        st.header("Input")
        st.caption(f"Project path: `{project_data_root}`")
        mode = st.radio("Choose source", ["Demo reports", "Upload PBIX"], index=0)

        analysis: Optional[ReportAnalysis] = None

        if mode == "Demo reports":
            if not demo_reports:
                st.warning(
                    "No demo data found. Expected either precomputed outputs under "
                    f"`{project_data_root}/powerbi-examples-all/report-query-logic` or Windows "
                    f"extract legacy reports under `{project_data_root}/*/windows-extract/legacy/Report`."
                )
            else:
                selected = st.selectbox("Demo report", sorted(demo_reports.keys()))
                analysis = demo_reports[selected]
                st.success(f"Loaded demo: {selected}")
                _render_upload_help()
                artifact_zip = st.file_uploader("Optional artifact ZIP (.dax/.bim)", type=["zip"])
                artifact_folder = st.text_input("Optional artifact folder path", value="")
                analysis = _maybe_enrich_with_artifacts(analysis, artifact_zip, artifact_folder)

        else:
            pbix_file = st.file_uploader("Upload PBIX", type=["pbix"])
            _render_upload_help()
            artifact_zip = st.file_uploader("Optional artifact ZIP (.dax/.bim)", type=["zip"], key="artifact_zip_upload")
            artifact_folder = st.text_input("Optional artifact folder path", value="", key="artifact_folder_upload")

            if pbix_file is not None:
                try:
                    analysis = analyze_pbix_bytes(pbix_file.name, pbix_file.getvalue())
                    analysis = _maybe_enrich_with_artifacts(analysis, artifact_zip, artifact_folder)
                    st.success("PBIX analyzed successfully.")
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")
                    analysis = None

    if analysis is None:
        st.warning("Select a demo report or upload a PBIX file to begin.")
        return

    tab_summary, tab_measures, tab_legacy, tab_downloads = st.tabs(
        ["Executive Summary", "Measure Logic", "Data Model Analysis", "Downloads"]
    )

    with tab_summary:
        st.caption(
            "Start here for high-level report shape and complexity. "
            "Then move to `Measure Logic` to inspect formula drivers."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Visual Queries", analysis.total_queries)
        c2.metric("Semantic Refs", analysis.total_refs)
        c3.metric("Unique Measures", analysis.unique_measures)
        c4.metric("Unique Columns", analysis.unique_columns)

        _render_executive_analytics_summary(analysis)

    with tab_measures:
        st.caption(
            "Use this tab to inspect key measures and formulas. "
            "Then open `Data Model Analysis` to trace table relationships."
        )
        st.subheader("Measure Logic Overview")
        df = _build_measure_table(analysis)
        dax_count = int(df["Has Formula"].sum()) if not df.empty else 0
        st.caption(f"DAX measures highlighted in selector: {dax_count}/{len(df)}")

        inspect_dax_only = st.checkbox("Inspect only DAX measures", value=False)
        inspect_df = df
        inspect_options = inspect_df["Measure"].tolist() if not inspect_df.empty else []
        if inspect_dax_only and not df.empty:
            inspect_options = inspect_df[inspect_df["Has Formula"]]["Measure"].tolist()

        selected_measure = st.selectbox(
            "Inspect measure",
            inspect_options,
            format_func=lambda name: _measure_label(analysis, name),
        )
        if selected_measure:
            selected_row = inspect_df[inspect_df["Measure"] == selected_measure].iloc[0]
            representative = selected_row.get("_Representative", selected_measure)
            detail = analysis.measures.get(representative) or analysis.measures[selected_measure]
            st.write(f"**Source:** `{detail.source}`")
            if detail.dax_formula:
                st.success("DAX-related measure (formula available).")
            st.write(f"**Complexity score:** {detail.complexity_score}")
            st.write(f"**Usage count:** {detail.usage_count}")
            st.write(f"**Sections:** {', '.join(detail.sections) if detail.sections else 'N/A'}")
            if detail.matched_tokens:
                st.write(f"**Matched tokens:** {', '.join(detail.matched_tokens)}")
            if detail.dax_formula:
                st.code(detail.dax_formula, language="sql")
            else:
                st.info("Full formula unavailable. This row is from semantic query references.")

        st.divider()
        if df.empty:
            st.info("No measure rows found for this report.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Measures (deduped)", len(df))
            m2.metric("With Formula", int(df["Has Formula"].sum()))
            m3.metric("Semantic Only", int((~df["Has Formula"]).sum()))
            m4.metric("Artifact Only", int(((df["Source"] == "dax") & (df["Usage Count"] == 0)).sum()))

            search_measure = st.text_input("Search measure", value="")
            source_filter = st.multiselect(
                "Source filter",
                options=sorted(df["Source"].unique().tolist()),
                default=sorted(df["Source"].unique().tolist()),
            )
            formula_filter = st.selectbox(
                "Formula filter",
                ["All", "Only with formula", "Only without formula"],
                index=0,
            )

            filtered_df = df.copy()
            if search_measure.strip():
                token = search_measure.strip().lower()
                filtered_df = filtered_df[
                    filtered_df["Measure"].str.lower().str.contains(token)
                    | filtered_df["Sections"].str.lower().str.contains(token)
                ]
            if source_filter:
                filtered_df = filtered_df[filtered_df["Source"].isin(source_filter)]
            if formula_filter == "Only with formula":
                filtered_df = filtered_df[filtered_df["Has Formula"]]
            elif formula_filter == "Only without formula":
                filtered_df = filtered_df[~filtered_df["Has Formula"]]

            st.caption(f"Rows shown: {len(filtered_df)} / {len(df)}")
            st.dataframe(
                filtered_df[["Measure", "Source", "Complexity", "Usage Count", "Sections", "Has Formula"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab_legacy:
        st.caption(
            "This tab explains model structure (tables, relationships, dictionary). "
            "Use it to connect measure logic back to model lineage."
        )
        _render_legacy_analysis(analysis)

    with tab_downloads:
        st.caption(
            "Download aligned outputs for sharing and audit: "
            "`Overview -> Executive -> Measure Logic -> Data Model Analysis`."
        )
        summary_md = build_markdown_summary(analysis)
        summary_json = _analysis_to_json(analysis)
        summary_excel = None
        excel_error = None
        try:
            summary_excel = _analysis_to_excel_bytes(analysis)
        except Exception as exc:
            excel_error = exc
        st.download_button(
            "Download summary markdown",
            data=summary_md,
            file_name=f"{analysis.report_name}_summary.md",
            mime="text/markdown",
        )
        st.download_button(
            "Download summary json",
            data=summary_json,
            file_name=f"{analysis.report_name}_summary.json",
            mime="application/json",
        )
        if summary_excel is not None:
            st.download_button(
                "Download summary excel",
                data=summary_excel,
                file_name=f"{analysis.report_name}_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning(f"Excel export unavailable: {excel_error}")


if __name__ == "__main__":
    main()
