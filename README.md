# SwiftClaim — AI Vehicle Damage Claims Platform

> **AI/ML Mini Project** — Computer Vision Insurance Intelligence  
> Tech: Python · OpenCV · Scikit-learn · Flask · React · SQLite

---

## 🏗️ Architecture Overview

```
ML - Mini project/
├── swiftclaim/backend/      ← Computer Vision claims engine (port 5001)
│   ├── app.py               Flask REST API
│   ├── damage_detector.py   OpenCV pipeline — detects damaged parts
│   ├── severity_estimator.py Edge/texture analysis → Minor/Moderate/Severe
│   ├── parts_database.py    SQLite parts-price catalogue
│   ├── payout_calculator.py Depreciation + labour + GST → payout
│   └── requirements.txt
│
├── frontend/                ← React 18 + Vite (port 5173)
│   └── src/
│       ├── pages/Home.jsx
│       └── pages/SwiftClaim.jsx
│
├── SETUP.bat                ← Run once to install everything
└── START.bat                ← Run to launch both services
```

---

## 🚀 Quick Start

### Prerequisites
- Python ≥ 3.9
- Node.js ≥ 18
- pip

### Step 1 — One-time setup
```bat
SETUP.bat
```
This installs Python + npm dependencies.

### Step 2 — Launch everything
```bat
START.bat
```
Opens two terminal windows and your browser at `http://localhost:5173`.

---

## 🚗 SwiftClaim Engine — How It Works

| Step | Module | Technology |
|------|--------|------------|
| 1. Upload photo | `app.py` | Flask multipart/form-data |
| 2. Detect parts | `damage_detector.py` | OpenCV Canny edges + contour analysis |
| 3. Score severity | `severity_estimator.py` | Laplacian variance + HSV std-dev |
| 4. Price lookup | `parts_database.py` | SQLite with 16 OEM/aftermarket prices |
| 5. Payout calc | `payout_calculator.py` | Depreciation table + GST + deductible |

**API Endpoints (port 5001):**
```
POST /api/upload-claim       → full pipeline result
GET  /api/parts-prices       → parts catalogue
GET  /api/claim/<id>         → claim by ID
GET  /api/stats              → aggregated claim stats
```

---

## 🎨 Frontend Routes

| URL | Page |
|-----|------|
| `/` | Landing page with SwiftClaim overview |
| `/swiftclaim` | Drag-and-drop claim upload + results |

---

## 🏗️ Business Value

**SwiftClaim** — Cuts claims settlement from days to seconds, eliminates manual fraud entry points, handles unstructured image data at scale. The full detection → severity → payout pipeline completes in under 2 seconds via the Flask REST API.
