# Data contract (inputs, meaning, and mapping to CLARO)

This document defines what data CLARO expects from the library (and/or external sources), and how each input is translated into the model-ready analytical table.

The key principle is: **raw data ≠ construct**. Raw inputs are treated as **proxies** mapped to CLARO constructs (X₁, X₂, X₃, Y).

---

## 1) Energy meter data (Y)

### Minimal required fields

- `timestamp` (ISO 8601 recommended)
- `energy_kwh` (energy consumed within the interval)

### Acceptable variants

- Cumulative meter readings (requires differencing)
- `energy_wh` (will be converted to kWh)

### Notes

- Timestamp timezone must be explicit or agreed (e.g., Europe/Warsaw)
- Resolution should be consistent (e.g., 15min, 30min, 1H)

**Mapping**

- Proxy → Construct: `energy_kwh` → **Y**

---

## 2) Human use proxy data (P₁ → X₁)

### Possible sources

- Entry counts per interval
- WiFi association counts
- Seat sensor occupancy
- Room booking intensity

### Minimal required fields

- `timestamp`
- `occupancy_proxy_value`
- `proxy_type` (optional but recommended)

**Mapping**

- Proxy → Construct: `occupancy_proxy_value` → **X₁ (Human use / occupancy)**

---

## 3) Environmental data (P₂ → X₂)

### Minimal required fields

- `timestamp`
- `temp_outdoor_c`

Optional:

- humidity
- wind speed

**Derived**

- `temp_pressure` = distance from comfort range

**Mapping**

- Proxy → Construct: `temp_outdoor_c` → **X₂ (Environmental conditions)**

---

## 4) Operational regime data (P₃ → X₃)

### Minimal required fields

One of the following formats is acceptable:

**A) Interval format**

- `timestamp_start`, `timestamp_end`
- `open` (0/1)

**B) Calendar format**

- `date`
- `open_hours_start`, `open_hours_end`

Optional:

- `extended_hours` (0/1)
- `special_event` (0/1)

**Mapping**

- Proxy → Construct: `open` / derived open flags → **X₃ (Operational regime)**

---

## 5) Structural building information (X₄) and systems context (X₅)

These inputs are typically static metadata rather than time series.

### Examples

- floor area, insulation indicators, age, HVAC type
- control logic (manual/automatic), retrofits

**Mapping**

- Metadata → Construct: building/system descriptors → **X₄ / X₅**

---

## 6) Target analytical table (model-ready)

One row per time interval (aligned to Y’s resolution).

### Required columns

- `timestamp`
- `Y_kwh`
- `X1_occupancy_proxy`
- `X2_temp_out`
- `X2_temp_pressure`
- `X3_open`

### Optional (recommended)

- calendar flags (exam period, holiday)
- regime flags (extended hours)
- simple lags for inertia representation (e.g., `Y_lag_1`, `Y_lag_24`)

---

## 7) Explicit exclusions (data governance)

- No personal identifiers
- No individual tracking
- Only aggregated operational signals
