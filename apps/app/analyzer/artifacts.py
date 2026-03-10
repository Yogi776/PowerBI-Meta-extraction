from __future__ import annotations

import pathlib
import tempfile
import zipfile
from io import BytesIO
from dataclasses import dataclass
from typing import Dict

from .models import MeasureDetail


@dataclass
class ArtifactParseResult:
    measures: Dict[str, MeasureDetail]
    has_bim: bool
    bim_location: str  # none | inside_folder | sibling_file
    dax_count: int


def _collect_from_folder(base: pathlib.Path) -> ArtifactParseResult:
    measures: Dict[str, MeasureDetail] = {}
    has_bim = False
    bim_location = "none"
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".bim":
            has_bim = True
            bim_location = "inside_folder"
        if path.suffix.lower() != ".dax":
            continue

        key = path.stem
        # Preserve folder context to avoid collisions for common names like "Total"
        rel_parent = str(path.parent.relative_to(base))
        name = f"{rel_parent}/{key}" if rel_parent != "." else key
        try:
            formula = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            formula = path.read_text(encoding="latin1").strip()

        measures[name] = MeasureDetail(
            name=name,
            source="dax",
            dax_formula=formula,
            usage_count=0,
            sections=[],
            matched_tokens=[],
            complexity_score=0,
        )

    # pbi-tools generate-bim commonly writes "<foldername>.bim" to the parent folder
    # (for example selecting ".../workflow-extract/legacy" creates ".../workflow-extract/legacy.bim").
    if not has_bim:
        sibling_bim = base.parent / f"{base.name}.bim"
        if sibling_bim.exists() and sibling_bim.is_file():
            has_bim = True
            bim_location = "sibling_file"

    return ArtifactParseResult(
        measures=measures,
        has_bim=has_bim,
        bim_location=bim_location,
        dax_count=len(measures),
    )


def parse_artifact_zip(artifact_bytes: bytes) -> ArtifactParseResult:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        with zipfile.ZipFile(BytesIO(artifact_bytes), "r") as zf:
            zf.extractall(root)
        return _collect_from_folder(root)


def parse_artifact_folder(folder_path: str) -> ArtifactParseResult:
    return _collect_from_folder(pathlib.Path(folder_path))
