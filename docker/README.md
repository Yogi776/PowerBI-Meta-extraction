# Linux / macOS Docker (pbi-tools Core)

This setup runs **on Mac and Linux** (and Windows with Linux containers). It uses **pbi-tools Core** in a Linux container.

- **Runs on:** macOS (Intel and Apple Silicon), Ubuntu/Linux, Windows with Docker Desktop in *Linux* container mode.
- **Does not support:** `extract` from `.pbix` (that requires Windows + Power BI Desktop; use [Windows containers](README.windows.md) for that).
- **Supports:** `generate-bim`, `convert`, and other Core actions on **already-extracted** folders.

## 1) Build (from repo root)

```bash
docker compose -f docker/compose.yml build
```

On Apple Silicon Mac, the image runs as `linux/amd64` (emulated).

## 2) Test

```bash
docker compose -f docker/compose.yml run --rm pbi-tools info
```

## 3) Generate BIM from an extracted folder

If you have an extracted folder (e.g. from a Windows run or CI), you can generate the `.bim` on Mac:

```bash
docker compose -f docker/compose.yml run --rm pbi-tools generate-bim out/MyReport/windows-extract/legacy
```

Output: `out/MyReport/windows-extract/legacy.bim`

## 4) Other Core commands

Run any pbi-tools Core command with:

```bash
docker compose -f docker/compose.yml run --rm pbi-tools <command> [options]
```

Example:

```bash
docker compose -f docker/compose.yml run --rm pbi-tools convert --help
```

## Summary

| Image              | Dockerfile           | Runs on              | Extract from .pbix |
|--------------------|----------------------|----------------------|--------------------|
| **pbi-tools-core** | `Dockerfile`         | Mac, Linux, Windows (Linux containers) | No  |
| **pbi-tools-win**  | `Dockerfile.windows` | Windows (Windows containers only)      | Yes |
