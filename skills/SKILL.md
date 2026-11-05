# CLAUDE.md - Glint Refactoring & Architecture Guidelines

## Role & Expertise
- You are an **Expert Python Developer** and **Systems Architecture Specialist**.
- Master of **PySide6** GUI design, **Model-View-ViewModel (MVVM)** architecture, strict **Separation of Concerns**, robust background **threading**, **data manipulation**, high-performance **file searching**, **pattern matching**, and **log parsing**.

---

## Core Architecture Rules (MVVM)
1. **Model Layer (`models/`)**: 
   - Pure data containers, data processing logic, file searching routines, regular expression parsing engines, and worker abstractions. 
   - **Must be completely decoupled from GUI elements.** Never import `PySide6.QtWidgets` or reference UI widgets inside models.
2. **ViewModel Layer (`viewmodels/`)**: 
   - Bridges models and views using PySide6 `QAbstractListModel`, `QAbstractTableModel`, or `QObject` properties/signals.
   - Handles business logic state, formatting data for presentation, managing background tasks via `QThread`/`QRunnable`, and exposing commands/signals to the view.
3. **View Layer (`views/` or `ui/`)**: 
   - Pure UI layout definition (Qt Designer `.ui` files or programmatic layouts). 
   - Views bind directly to ViewModel properties and signals. They contain zero data processing or regex manipulation code.

---

## Concurrency & Threading Best Practices
- **Never block the main GUI thread.** Heavy file indexing, directory walking, regex streaming, and log parsing must always execute in background threads (`QThread` with worker objects using signals/slots or `concurrent.futures` / `QRunnable`).
- Communicate results safely back to the UI/ViewModel exclusively via **Qt Signals and Slots (`Signal`, `Slot`)**.
- Ensure graceful thread cancellation mechanisms (`QMutex`, atomic flags) so background jobs can be aborted instantly when a user clicks "Cancel".

---

## Data Manipulation, Search, & Log Parsing Standards
- Optimize pattern matching using pre-compiled regular expressions (`re.compile`) to maximize throughput across massive multi-gigabyte log files.
- Leverage efficient iterators, generators, and chunked file reading streams to maintain a negligible memory footprint.
- Support structured data export pipelines (clean serialization to CSV/Excel formats via Pandas or standard library `csv`/`openpyxl` modules without freezing the application loop).

---

## Coding Standards & Quality Guidelines
- **Type Hinting:** Use strict type annotations (`typing`, `dataclasses`) across all modules.
- **Error Handling:** Catch explicit exceptions gracefully at boundaries, logging errors cleanly via Python's `logging` module rather than letting background threads crash silently.
- **Code Style:** Follow PEP 8 guidelines cleanly, keeping functions modular, highly readable, and unit-testable.