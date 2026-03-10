# Streamlit PowerBI Analyzer

Demo app to analyze Power BI reports with:
- semantic query analysis from `Report/Layout` (cross-platform),
- optional full DAX/BIM enrichment from extracted artifacts,
- built-in demo dataset from `PowerBI Examples`.

## Run

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/pbi_analyzer/requirements.txt
streamlit run apps/pbi_analyzer/app.py
```

## Run with Docker (copy `out` into image)

Build from repo root:

```bash
docker build -f apps/pbi_analyzer/Dockerfile -t pbi-analyzer .
```

Run container (data already embedded in image):

```bash
docker run --rm -p 8501:8501 pbi-analyzer
```

Then open `http://localhost:8501`.

## Supported Inputs

- Upload PBIX: semantic query extraction (`queryRef`, section usage, complexity candidates).
- Upload artifact ZIP (optional): if it contains `.dax` and `.bim` files, app enriches measure logic with formula bodies.
- Optional GitHub Actions handoff panel: trigger Windows extraction workflow and check latest run status.
- Demo mode fallback: reads legacy outputs from `out/*/windows-extract/legacy` (including `Model/tables/*/measures/*.dax`).

## Downloads

- Markdown summary (`.md`)
- JSON summary (`.json`)
- Excel summary (`.xlsx`) with sheets for Overview, Sections, Measures, VisualQueries, SemanticReferences, LegacyCounts, LegacyTables, LegacyQueries, LegacyDiagram

## Legacy Analysis Tab

- Deep analysis for `out/*/windows-extract/legacy` reports
- Includes model table inventory, DAX measure inventory, Power Query inventory, metadata/connections summary, and a flow diagram

## Full Dashboard Documentation

See `apps/pbi_analyzer/DASHBOARD_DOCUMENTATION.md` for the single complete dashboard document.

## Hybrid Flow (Docker + Windows)

1. Upload PBIX in app for immediate semantic analysis.
2. Trigger Windows workflow from sidebar panel (`extract-pbix-model.yml`) to produce full extraction artifacts.
3. Download `pbix-extract-artifacts` from the workflow run.
4. Load artifact ZIP (or extracted folder) in app to enrich with `.dax` formulas and BIM presence.

The app shows pipeline states:
- `SemanticReady`
- `ArtifactLoaded`
- `DaxEnriched`

## Demo Data

The app auto-loads precomputed outputs from:

`out/powerbi-examples-all/report-query-logic`

and shows them in the report selector even without uploads.

## Notes

- Full DAX formula extraction is only available when `.dax` files are provided (for example from the Windows extraction workflow).
- Without `.dax`, the app still provides usage-level logic analysis from report semantic queries.
- GitHub Actions trigger requires a token and PBIX paths that already exist in the repository.
- Docker-only mode cannot produce PBIX `extract` output (`.dax` + `.bim`) because `pbi-tools.core` does not support the PBIX `extract` action.
- `generate-bim` only works when valid model sources are already present.
