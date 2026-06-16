"""Project-wide constants and skill dictionaries.

The configuration now includes:
* ``SKILL_CATEGORIES`` – grouped skill sets used for category‑aware analysis.
* ``SKILL_ALIASES`` – maps common aliases or abbreviations to the canonical skill name.
* ``SKILL_SYNONYMS`` – maps a skill to a set of related terms for partial matching.
* ``FLATTENED_SKILL_SET`` – a fast‑lookup set containing all canonical skill names and aliases.
"""

# ---------------------------------------------------------------------------
# Skill categories (canonical skill names are lower‑case strings)
# ---------------------------------------------------------------------------
SKILL_CATEGORIES = {
    "Programming Languages": {
        "python",
        "java",
        "c",
        "c++",
        "c#",
        "html",
        "css",
        "javascript",
        "typescript",
        "php",
        "go",
        "rust",
        "kotlin",
    },
    "Frameworks": {
        "spring",
        "springboot",
        "asp.net",
        "django",
        "flask",
        "fastapi",
        "angular",
        "react",
        "vue",
    },
    "Databases": {
        "mysql",
        "postgresql",
        "sql server",
        "mongodb",
        "redis",
    },
    "DevOps": {"docker", "kubernetes", "jenkins", "github actions", "gitlab ci"},
    "Cloud": {"aws", "azure", "gcp"},
    "Tools": {"git", "linux", "postman", "kafka", "rabbitmq", "restapi"},
    "Testing": {"junit", "pytest", "nunit"},
    "Soft Skills": {"teamwork", "communication", "leadership", "problem solving"},
}

# ---------------------------------------------------------------------------
# Aliases – map alternative spellings / abbreviations to the canonical name
# ---------------------------------------------------------------------------
SKILL_ALIASES = {
    "csharp": "c#",
    "c#": "c#",
    "c++": "c++",
    "js": "javascript",
    "ts": "typescript",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "sqlserver": "sql server",
    "postgres": "postgresql",
    "mssql": "sql server",
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "github": "git",
    "gitlab": "git",
    "restapi": "restapi",
    "rest-api": "restapi",
    "spring": "springboot",
}

# ---------------------------------------------------------------------------
# Synonyms – related terms that give a *partial* match credit.
# Example: "spring" is a synonym of "springboot" and vice‑versa.
# ---------------------------------------------------------------------------
SKILL_SYNONYMS = {
    "springboot": {"spring"},
    "spring": {"springboot"},
    "react": {"reactjs", "react.js"},
    "angular": {"angularjs"},
    "vue": {"vuejs"},
    "docker": {"container"},
    "kubernetes": {"k8s"},
    "restapi": {"rest api", "restful api"},
}

# ---------------------------------------------------------------------------
# Flattened set for fast existence checks (includes canonical names and aliases)
# ---------------------------------------------------------------------------
# Start with all canonical skills from all categories
_canonical = set().union(*SKILL_CATEGORIES.values())
# Add alias target values (they are already canonical, but ensure inclusion)
_alias_targets = set(SKILL_ALIASES.values())
FLATTENED_SKILL_SET = _canonical.union(_alias_targets)
