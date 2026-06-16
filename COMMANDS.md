# SkillMatch – Development Commands

This repository follows a simple command‑based workflow. The commands work on any
platform that has **Python** (3.9+) installed. On Windows you can run them from
PowerShell or `cmd.exe`.

## 1. Install dependencies
```bash
python -m venv .venv
# Activate the virtual environment
# PowerShell:
.venv\Scripts\Activate.ps1
# cmd.exe:
.venv\Scripts\activate.bat
# Bash (Git‑Bash, WSL, etc.):
source .venv/bin/activate

pip install -e .[test]
```

The `-e .` flag installs the package in editable mode so that changes are reflected
immediately. The optional `test` extra brings in **pytest** and **pytest‑cov**.

## 2. Run the application
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## 3. Run the test suite
```bash
pytest
```

Tests are located in the **tests/** directory and cover extraction, alias/synonym
handling, compatibility scoring and edge‑case scenarios.

---
*Tip*: After activating the virtual environment you can also use the shortcuts in
the **Makefile** (if you have `make` installed) – see the optional `Makefile`
section below.
