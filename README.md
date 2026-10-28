# Multimodal Construction Intelligence Platform

Skill Wallet Capstone Project 1: a Streamlit decision-support app for construction sites.

## Features
- **Site Safety & PPE Audit**: upload a site photo, get a safety score, PPE checklist and hazards (JSON, downloadable).
- **Crack Diagnostics**: classifies defect type, estimates crack width, root causes, repairs, urgency.
- **Planning & Valuation**: budget, capex incurred, market valuation in INR, steel/cement estimate, Pollinations concept render.
- **Site Assistant**: weather-aware safety advisory plus a multi-turn engineering chatbot.
- **Demo mode** when no Gemini API key is supplied.

## Tech stack
Python 3.9+, Streamlit, Google Gemini (multimodal), Pillow, JSON data contracts.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to a public GitHub repo, then share.streamlit.io -> New app -> select `app.py`.

## Known limitations
Cost and valuation figures are rough heuristics, not professional estimates. AI output must be verified by a qualified engineer.
