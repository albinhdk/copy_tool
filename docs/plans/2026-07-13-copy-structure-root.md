# Configurable Copy Structure Root Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Replace the Vue-only path rewrite with an automatically detected, manually selectable copy structure root that is remembered per Git repository.

**Architecture:** `FileService` owns pure path candidate detection, output-path mapping, and collision validation. `MainWindow` exposes a structure-root selector, while `MainController` refreshes candidates after scans, persists explicit selections per repository, and passes the resolved root into the existing asynchronous copy workflow. Files outside the selected root retain their repository-relative paths.

**Tech Stack:** Python, PySide6, QSettings, pytest, PyInstaller

---

### Task 1: Path mapping and detection

**Files:**
- Modify: `src/services/file_service.py`
- Modify: `tests/test_file_service.py`

1. Add failing tests for Vue, Maven/Gradle, common-root fallback, outside-root preservation, and output collisions.
2. Run `pytest tests/test_file_service.py -q` and confirm the new tests fail.
3. Implement normalized relative-path mapping, known source-root detection, and collision reporting.
4. Run the file-service tests and confirm they pass.

### Task 2: Per-repository persistence

**Files:**
- Modify: `src/services/config_service.py`
- Modify: `tests/test_config_service.py`

1. Add tests showing two repositories retain independent structure-root choices.
2. Store choices under a stable hash of the normalized repository path.
3. Run `pytest tests/test_config_service.py -q`.

### Task 3: UI and controller integration

**Files:**
- Modify: `src/views/main_window.py`
- Modify: `src/controllers/main_controller.py`
- Modify: `src/workers/copy_worker.py`
- Modify: `tests/test_main_controller.py`

1. Add a selector with automatic candidate text, repository-root fallback, detected candidates, and a browse button.
2. Refresh candidates after every successful Git scan and restore a saved selection when available.
3. Pass the selected relative root into `CopyWorker` and then `FileService.copy_files`.
4. Show the resolved structure root in success messages and report path collisions as copy errors.
5. Run controller tests and inspect the rendered window.

### Task 4: Verification and packaging

**Files:**
- Use: `GitCopyTool.spec`

1. Run the full pytest suite.
2. Build with `pyinstaller --clean --noconfirm GitCopyTool.spec`.
3. Confirm `dist/GitCopyTool.exe` exists, has a current timestamp, and launches without an immediate error.

