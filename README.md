# Smart, Priority-Aware Emergency Response System

A web-based emergency response demo that prioritizes incidents, simulates ETA using traffic-aware logic, and dispatches the optimal emergency resource (ambulance or fire & rescue) for academic evaluation.

## Project Structure

```
EMS/
├── app.py
├── db.py
├── ems.db (generated at runtime)
├── requirements.txt
├── schema.sql
├── seed.sql
├── static/
│   ├── app.js
│   └── styles.css
└── templates/
    └── index.html
```

## Features

- Emergency incident intake form and REST API.
- Dynamic priority scoring (0–100) based on severity, victims, type, and time sensitivity.
- ETA estimation using distance, simulated traffic, and readiness time.
- Resource dispatch optimization based on ETA (not just nearest unit).
- Dashboard view for incident details and dispatch decision.

## Database Schema

Tables are defined in `schema.sql`:

- `incidents`: incident intake and priority scores.
- `resources`: emergency units and readiness/position.
- `dispatch_logs`: dispatch decisions and ETA.

## API Endpoints

- `GET /api/resources` — list emergency resources.
- `GET /api/incidents` — list incidents.
- `POST /api/incidents` — create an incident and trigger dispatch.
- `GET /api/dispatch/<incident_id>` — re-run dispatch for an incident.

## Priority Score Logic

The priority score is computed dynamically with weighted contributions:

- Severity weight
- Emergency type weight
- Victim count factor
- Time sensitivity factor

The final score is normalized to a 0–100 scale for easy comparison.

## ETA Logic

ETA is calculated as:

```
ETA = travel_time + traffic_delay + readiness_time
```

Traffic delay is simulated deterministically, so the demo behaves consistently without paid APIs.

## Setup & Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open your browser at: `http://localhost:5000`

## Sample Test Data

Sample emergency resources are inserted automatically from `seed.sql` when the app starts. You can submit incidents through the UI form.

## Notes

- This project uses SQLite for simplicity.
- Logic is intentionally clear and modular for viva and academic review.
