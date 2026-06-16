"""Entry point for the SkillMatch Streamlit application.

Running ``streamlit run app.py`` will launch the web UI defined in
``src.skillmatch.adapters.streamlit_ui``.
"""

# Streamlit works best when the import of the UI module happens inside the
# ``if __name__ == "__main__"`` guard.  This avoids import side‑effects when the
# file is scanned by tools.

if __name__ == "__main__":
    from src.skillmatch.adapters.streamlit_ui import run

    run()
