# SkillMatch

**SkillMatch** es una aplicación web desarrollada en Python y Streamlit que utiliza Inteligencia Artificial (Google Gemini) para analizar la compatibilidad entre una oferta de empleo y el perfil de un candidato.

La herramienta extrae automáticamente requisitos, habilidades, experiencia y nivel profesional a partir de texto libre, generando un análisis detallado que ayuda tanto a candidatos como a reclutadores a identificar fortalezas, carencias y oportunidades de mejora.

---

# Características principales

### Análisis mediante IA

* Extracción automática de información desde ofertas de empleo reales.
* Análisis de currículums y perfiles profesionales.
* Identificación de tecnologías, experiencia requerida y nivel profesional.
* Compatible con descripciones extensas y no estructuradas.

### Sistema de puntuación inteligente

SkillMatch calcula diferentes métricas:

* **Skills Score** (habilidades técnicas)
* **Experience Score** (experiencia)
* **Seniority Score** (nivel profesional)
* **Final Score** (compatibilidad global)

La extracción es realizada por Gemini, mientras que la lógica de puntuación es calculada por Python para mantener resultados consistentes y transparentes.

### Análisis de habilidades

Clasificación automática de:

* Coincidencias fuertes
* Coincidencias parciales
* Habilidades faltantes

Además, distingue entre:

* Experiencia profesional real
* Experiencia en prácticas
* Experiencia en proyectos personales
* Requisitos no cumplidos

### Recomendaciones personalizadas

La aplicación genera automáticamente:

* Explicación del resultado obtenido
* Recomendaciones de contratación
* Consejos para entrevistas
* Roadmap de aprendizaje personalizado

### Dashboard visual

Incluye:

* Tarjetas resumen de puntuación
* Análisis de habilidades
* Desglose por categorías
* Recomendaciones visuales
* Exportación de resultados

### Exportación

Los análisis pueden descargarse en:

* Markdown
* JSON

---

# Tecnologías utilizadas

## Backend

* Python 3
* Streamlit

## Inteligencia Artificial

* Google Gemini API

## Procesamiento de datos

* Pydantic
* Sistema de scoring personalizado

## Visualización

* Plotly

## Testing

* Pytest

---

# Capturas de pantalla

## Pantalla principal

<img width="1905" height="845" alt="image" src="https://github.com/user-attachments/assets/6c0d3891-49c5-451d-b1f6-e94aaec62f99" />

## Resultado del análisis

<img width="1609" height="824" alt="image" src="https://github.com/user-attachments/assets/f85af9e1-7b60-4231-b828-4fb618cb75a3" />
<img width="884" height="855" alt="image" src="https://github.com/user-attachments/assets/33b8a67f-669e-4bb9-af52-9bec79061423" />

## Recomendaciones y roadmap

<img width="1466" height="661" alt="image" src="https://github.com/user-attachments/assets/714ee6cc-b1db-4070-8d65-59a99034ec7e" />

---

# Instalación

## Clonar repositorio

```bash
git clone https://github.com/ManuelTagua/SkillMatch.git
cd SkillMatch
```

## Crear entorno virtual

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Configuración de Gemini

Crear una variable de entorno con la clave de Gemini:

```bash
GEMINI_API_KEY
```

La clave nunca debe subirse al repositorio.

---

# Ejecución

```bash
streamlit run app.py
```

Abrir posteriormente:

```text
http://localhost:8501
```

---

# Casos de uso

## Para candidatos

* Comparar un CV con una oferta laboral.
* Detectar habilidades faltantes.
* Priorizar tecnologías a estudiar.
* Preparar entrevistas técnicas.

## Para reclutadores

* Evaluar rápidamente candidatos.
* Detectar carencias técnicas.
* Analizar experiencia y seniority.
* Obtener recomendaciones de contratación.

---

# Estructura del proyecto

```text
SkillMatch/
│
├── app.py
├── requirements.txt
├── README.md
│
├── src/
│   └── skillmatch/
│       ├── adapters/
│       ├── ai/
│       ├── config/
│       ├── domain/
│       └── services/
│
├── tests/
│
└── data/
```

---

# Mejoras futuras

* Soporte multiidioma
* Análisis masivo de currículums
* Importación directa de PDFs
* Sistema ATS avanzado
* Ranking automático de candidatos
* Dashboard para equipos de RRHH
* Despliegue en la nube

---

# Autor

**Manuel Tagua Pérez**

Técnico Superior en Desarrollo de Aplicaciones Multiplataforma (DAM)

Proyecto desarrollado como parte de mi portfolio profesional para demostrar conocimientos en:

* Desarrollo con Python
* Integración de Inteligencia Artificial
* Prompt Engineering
* Arquitectura de software
* Visualización de datos
* Desarrollo de aplicaciones web
