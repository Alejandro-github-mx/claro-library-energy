cat > README.md << 'EOF'

# CLARO — Library Energy Consumption (Conceptual + Reproducible Prototype)

CLARO models the real-world phenomenon by which a university library consumes electricity over time as an emergent outcome of human use, external environmental pressure, institutional operating regimes, technical system behavior, and physical/temporal constraints.

This repository is intentionally designed for review: it contains (1) the conceptual structure (phenomenon → variables → DAG → hypotheses), (2) a reproducible simulation that mirrors the causal story, and (3) a data pipeline skeleton ready to ingest real library-provided data once available.

---

## What problem is CLARO solving?

CLARO is not “energy forecasting” in the abstract. It aims to learn an **explainable and stable structure** of energy consumption, separating:

- legitimate demand from **human use**
- exogenous pressure from **environmental conditions**
- institutional baselines from **operational regimes**
- structural constraints from **building properties**
- temporal memory from **system inertia**

---

## Conceptual model (high-level)

### Outcome (Y)

- **Y — Library energy consumption**: aggregated electricity consumption over a time interval.

### Core causal drivers (X)

- **X₁ — Human use / occupancy**
- **X₂ — External environmental conditions (primarily outdoor temperature)**
- **X₃ — Operational state / institutional operating regime**
- **X₄ — Physical characteristics of the building**
- **X₅ — State and configuration of technical systems**
- **X₆ — Physical and temporal inertia**

### Confounding and mediation

- **C₁ — Academic calendar / institutional seasonality** (confounder)
- **M₁ — System activation intensity** (mediator)

Full documentation: see `docs/`.

---

## What “success” means here

CLARO defines success as:

- stable, interpretable relationships consistent with the causal story
- robustness across time blocks and operating regimes
- diagnostics that expose confounding, leakage, and overcontrol

High predictive accuracy alone is not considered “learning”.

---

## Repository structure

- `docs/` — phenomenon, variables, DAG, hypotheses, pitfalls
- `src/claro/` — simulation + feature-building + diagnostics modules
- `data/` — never includes real data in this public repo (see `data/README.md`)
- `notebooks/` — sanity checks and dry runs
- `tests/` — lightweight tests for simulation and feature building

---

## Quick start (simulation)

### 1) Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Generate a simulated dataset

`python -m src.scripts.simulate_dataset --out data/simulated/claro_simulated.csv --n_days 60 --freq "60" --seed 123`

### 3) Inspect outputs

`head -n 5 data/simulated/claro_simulated.csv`

---

## Data governance

This public repository does not include any real library data.

- Real data should be stored locally under `data/raw/` (gitignored)

- Intermediate and processed outputs are also gitignored

- Only simulated data may be committed for reproducibility

---

## License

- Code: MIT (`LICENSE`)

- Documentation and figures: CC BY 4.0 (`LICENSE-CC-BY-4.0.md`)

---

## Submission context

This repository was prepared as part of an EUonAir application to demonstrate conceptual clarity, reproducibility, and readiness to integrate real data once provided.  

`cat > LICENSE-CC-BY-4.0.md << 'EOF' Creative Commons Attribution 4.0 International (CC BY 4.0) TODO: Paste the full CC BY 4.0 text here, or link + short notice. EOF`
