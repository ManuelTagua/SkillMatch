# SkillMatch

**SkillMatch** is a lightweight Streamlit web application that lets developers compare their skill set against a job posting.

## Features (Version 1)
- Paste a job offer description and your own profile (CV, skills list, etc.)
- Automatic extraction of technical skills from plain text
- Compatibility percentage based on matching skills
- Lists of matching and missing skills
- Simple recommendations on which missing skills would improve the score
- Visualisation with Plotly (progress bar & pie chart)

## Quick start
```bash
# clone the repo and cd into the project folder
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit (normally http://localhost:8501) and start analyzing job offers!

## Project structure (Version 1)
```
SkillMatch/
│   app.py                # Streamlit entry point
│   requirements.txt
│   README.md
└─ src/
   └─ skillmatch/
       ├─ __init__.py
       ├─ adapters/
       │   ├─ __init__.py
       │   ├─ streamlit_ui.py   # UI components & callbacks
       │   └─ plotters.py       # Plotly helper functions
       ├─ domain/
       │   ├─ __init__.py
       │   ├─ entities.py       # Data classes
       │   └─ services.py       # Skill extraction & compatibility logic
       └─ config/
           └─ settings.py       # Skill dictionary & constants
```

## Future roadmap
- Persist analyses with SQLite
- Smarter skill extraction using LLMs or NLP libraries
- User authentication and profile saving
- More detailed visual dashboards and export options
