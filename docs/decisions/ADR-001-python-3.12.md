# ADR-001: Use Python 3.12 instead of 3.13

**Status:** Accepted  
**Date:** 2026-11-16

## Context
The spec requires Python 3.11/3.12. The machine initially had Python 3.13, but installing the standard Python 3.13 installer was blocked by Windows security. We needed a Python version compatible with PaddleOCR and faster-whisper.

## Decision
We installed Python 3.12.10 via the Microsoft Store. This version supports all required packages and avoids Windows security blocks. We use `python3.12` explicitly and run the app in a dedicated `.venv`.

## Consequences
- ✅ Full compatibility with P0 benchmarks.
- ✅ No need to disable Smart App Control.
- ⚠️ Must always run via `.venv\Scripts\python.exe`; system 3.13 is unused.