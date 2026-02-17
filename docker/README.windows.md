# Windows Docker Usage (Full Extract)

Use this setup on a **Windows machine** with Docker Desktop running in **Windows containers** mode.

## 1) Switch Docker Desktop to Windows Containers

- Docker Desktop tray icon -> `Switch to Windows containers...`

## 1.1) Runtime precheck

Before building, confirm Docker is actually using Windows containers.

```powershell
docker version
docker info
```

Quick check:
- Output should indicate Windows container runtime context.
- If you see Linux/runc context, switch Docker Desktop to Windows containers first.

## 2) Build and test

From repo root:

```powershell
docker compose -f docker/compose.windows.yml run --rm pbi-tools-win info
```

## 3) Extract PBIX with DAX files

```powershell
docker compose -f docker/compose.windows.yml run --rm pbi-tools-win extract "PowerBI Examples\Territory Tracker -Slim.pbix" -extractFolder "out\workflow-extract\legacy" -modelSerialization Legacy
```

## 4) Generate BIM

```powershell
docker compose -f docker/compose.windows.yml run --rm pbi-tools-win generate-bim "out\workflow-extract\legacy"
```

Expected output path:

- `out\workflow-extract\legacy.bim`
- DAX files under `out\workflow-extract\legacy\...\*.dax`

## Notes

- This does not run on macOS/Linux Docker engines.
- If you are on macOS/Linux, use the app's GitHub Windows workflow handoff for full DAX/BIM extraction.
