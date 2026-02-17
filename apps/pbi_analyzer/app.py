from __future__ import annotations

import json
import pathlib
import time
from typing import Dict, Optional

import pandas as pd
import streamlit as st

from analyzer.artifacts import ArtifactParseResult, parse_artifact_folder, parse_artifact_zip
from analyzer.demo_loader import load_demo_reports
from analyzer.engine import build_markdown_summary, merge_dax_into_analysis, repo_root_from_app
from analyzer.github_actions import artifacts_for_run, latest_workflow_run, trigger_extract_workflow
from analyzer.models import ReportAnalysis
from analyzer.semantic import analyze_pbix_bytes


st.set_page_config(page_title="PowerBI Analyzer Demo", layout="wide")


def _render_source_badges(analysis: ReportAnalysis) -> None:
    cols = st.columns(4)
    cols[0].metric("Source mode", analysis.source_mode)
    cols[1].metric("DAX formulas", "Yes" if analysis.has_dax_formulas else "No")
    cols[2].metric("BIM detected", "Yes" if analysis.has_bim else "No")
    cols[3].metric("Measures tracked", len(analysis.measures))


def _analysis_to_json(analysis: ReportAnalysis) -> str:
    payload = {
        "report_name": analysis.report_name,
        "source_mode": analysis.source_mode,
        "total_queries": analysis.total_queries,
        "total_refs": analysis.total_refs,
        "unique_measures": analysis.unique_measures,
        "unique_columns": analysis.unique_columns,
        "has_dax_formulas": analysis.has_dax_formulas,
        "has_bim": analysis.has_bim,
        "section_summaries": [
            {
                "section": s.section,
                "unique_refs": s.unique_refs,
                "complexity_score": s.complexity_score,
            }
            for s in analysis.section_summaries
        ],
        "measures": [
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
    }
    return json.dumps(payload, indent=2)


def _build_measure_table(analysis: ReportAnalysis) -> pd.DataFrame:
    rows = []
    for m in analysis.top_measures(200):
        rows.append(
            {
                "Measure": m.name,
                "Source": m.source,
                "Complexity": m.complexity_score,
                "Usage Count": m.usage_count,
                "Sections": ", ".join(m.sections),
                "Has Formula": bool(m.dax_formula),
            }
        )
    return pd.DataFrame(rows)


def _render_upload_help() -> None:
    st.info(
        "For full DAX formulas, provide extraction artifacts containing `.dax` files "
        "(for example from `.github/workflows/extract-pbix-model.yml`). "
        "Without artifacts, app uses semantic query refs from `Report/Layout`."
    )


def _render_hybrid_status(analysis: Optional[ReportAnalysis]) -> None:
    st.subheader("Hybrid Pipeline Status")
    status_items = []
    if analysis is None:
        status_items.append(("SemanticReady", "No"))
        status_items.append(("ArtifactLoaded", "No"))
        status_items.append(("DaxEnriched", "No"))
    else:
        status_items.append(("SemanticReady", "Yes"))
        status_items.append(("ArtifactLoaded", "Yes" if analysis.has_dax_formulas or analysis.has_bim else "No"))
        status_items.append(("DaxEnriched", "Yes" if analysis.has_dax_formulas else "No"))

    cols = st.columns(3)
    for idx, (k, v) in enumerate(status_items):
        cols[idx].metric(k, v)

    if analysis is not None and not analysis.has_dax_formulas:
        st.info("Local Docker provides semantic analysis. Full DAX formulas require Windows extraction artifacts.")


def _render_actions_handoff_panel() -> None:
    with st.expander("Windows full extract via GitHub Actions", expanded=False):
        st.caption(
            "Triggers `.github/workflows/extract-pbix-model.yml` on Windows to generate full "
            "`.dax` and `.bim` artifacts."
        )
        st.warning(
            "Workflow can only process PBIX files that exist in your repository. "
            "If you upload a local PBIX in this app, commit it (or point to an existing repo path) first."
        )
        repo = st.text_input("GitHub repo (owner/name)", value="pbi-tools/pbi-tools")
        workflow_file = st.text_input(
            "Workflow file name", value="extract-pbix-model.yml"
        )
        git_ref = st.text_input("Git ref (branch/tag)", value="main")
        gh_token = st.text_input("GitHub token", value="", type="password")
        run_all = st.checkbox("Run for all PBIX in PowerBI Examples", value=False)
        pbix_path = st.text_input(
            "PBIX path in repo",
            value="PowerBI Examples/Territory Tracker -Slim.pbix",
        )
        model_serialization = st.selectbox(
            "Model serialization",
            ["Legacy", "Tmdl", "Raw", "Default"],
            index=0,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Trigger extraction workflow"):
                if not gh_token.strip():
                    st.error("GitHub token is required.")
                else:
                    try:
                        trigger_extract_workflow(
                            repo=repo.strip(),
                            workflow_file=workflow_file.strip(),
                            token=gh_token.strip(),
                            ref=git_ref.strip(),
                            run_all=run_all,
                            pbix_path=pbix_path.strip(),
                            model_serialization=model_serialization,
                        )
                        st.success("Workflow triggered successfully.")
                    except Exception as exc:
                        st.error(f"Failed to trigger workflow: {exc}")

        with c2:
            if st.button("Check latest workflow run"):
                if not gh_token.strip():
                    st.error("GitHub token is required.")
                else:
                    try:
                        run = latest_workflow_run(
                            repo=repo.strip(),
                            workflow_file=workflow_file.strip(),
                            token=gh_token.strip(),
                        )
                        if not run:
                            st.info("No workflow runs found.")
                        else:
                            st.write(
                                {
                                    "id": run.get("id"),
                                    "status": run.get("status"),
                                    "conclusion": run.get("conclusion"),
                                    "created_at": run.get("created_at"),
                                    "updated_at": run.get("updated_at"),
                                    "html_url": run.get("html_url"),
                                }
                            )
                            run_id = run.get("id")
                            if run_id:
                                artifacts = artifacts_for_run(
                                    repo=repo.strip(),
                                    run_id=int(run_id),
                                    token=gh_token.strip(),
                                )
                                names = [a.get("name") for a in artifacts.get("artifacts", [])]
                                st.write({"artifacts": names})
                                if run.get("conclusion") == "success":
                                    st.success(
                                        "Workflow succeeded. Download artifact `pbix-extract-artifacts` "
                                        "from the run page, then load it in this app."
                                    )
                    except Exception as exc:
                        st.error(f"Failed to fetch workflow run: {exc}")

        auto_poll = st.checkbox("Auto-poll latest run every 15s", value=False)
        if auto_poll and gh_token.strip():
            try:
                run = latest_workflow_run(
                    repo=repo.strip(),
                    workflow_file=workflow_file.strip(),
                    token=gh_token.strip(),
                )
                if run:
                    st.caption(
                        f"Latest run: status={run.get('status')} conclusion={run.get('conclusion')} "
                        f"url={run.get('html_url')}"
                    )
                time.sleep(15)
                st.rerun()
            except Exception as exc:
                st.error(f"Auto-poll failed: {exc}")


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
    demo_reports: Dict[str, ReportAnalysis] = load_demo_reports(root)

    with st.sidebar:
        st.header("Input")
        mode = st.radio("Choose source", ["Demo reports", "Upload PBIX"], index=0)
        _render_actions_handoff_panel()

        analysis: Optional[ReportAnalysis] = None

        if mode == "Demo reports":
            if not demo_reports:
                st.warning("No precomputed demo data found under out/powerbi-examples-all/report-query-logic.")
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

    _render_hybrid_status(analysis)
    _render_source_badges(analysis)

    tab_summary, tab_measures, tab_drilldown, tab_downloads = st.tabs(
        ["Executive Summary", "Measure Logic", "Section Drilldown", "Downloads"]
    )

    with tab_summary:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Visual Queries", analysis.total_queries)
        c2.metric("Semantic Refs", analysis.total_refs)
        c3.metric("Unique Measures", analysis.unique_measures)
        c4.metric("Unique Columns", analysis.unique_columns)

        st.subheader("Top Logic-Dense Sections")
        sec_rows = [
            {
                "Section": s.section,
                "Complexity Score": s.complexity_score,
                "Unique Refs": s.unique_refs,
            }
            for s in analysis.section_summaries[:25]
        ]
        st.dataframe(pd.DataFrame(sec_rows), use_container_width=True)

    with tab_measures:
        st.subheader("Measure Logic Overview")
        df = _build_measure_table(analysis)
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            artifact_only = df[(df["Source"] == "dax") & (df["Usage Count"] == 0)]
            if not artifact_only.empty:
                st.subheader("Artifact-only measures (not matched in queryRef)")
                st.dataframe(artifact_only, use_container_width=True)

        selected_measure = st.selectbox("Inspect measure", df["Measure"].tolist() if not df.empty else [])
        if selected_measure:
            detail = analysis.measures[selected_measure]
            st.write(f"**Source:** `{detail.source}`")
            st.write(f"**Complexity score:** {detail.complexity_score}")
            st.write(f"**Usage count:** {detail.usage_count}")
            st.write(f"**Sections:** {', '.join(detail.sections) if detail.sections else 'N/A'}")
            if detail.matched_tokens:
                st.write(f"**Matched tokens:** {', '.join(detail.matched_tokens)}")
            if detail.dax_formula:
                st.code(detail.dax_formula, language="sql")
            else:
                st.info("Full formula unavailable. This row is from semantic query references.")

    with tab_drilldown:
        st.subheader("Visual / Section Drilldown")
        section_names = sorted({q.get("section", "Unknown") for q in analysis.visual_queries})
        selected_section = st.selectbox("Section", section_names)
        section_queries = [q for q in analysis.visual_queries if q.get("section") == selected_section]
        st.write(f"Visual query objects in section: **{len(section_queries)}**")
        st.json(section_queries[:8])

        st.subheader("Semantic References Sample")
        st.json(analysis.semantic_references[:60])

    with tab_downloads:
        summary_md = build_markdown_summary(analysis)
        summary_json = _analysis_to_json(analysis)
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


if __name__ == "__main__":
    main()
