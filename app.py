from datetime import datetime, timezone
import math
from flask import Flask, jsonify, render_template, request

from db import get_connection, init_db

app = Flask(__name__)

SEVERITY_WEIGHTS = {
    "Low": 10,
    "Medium": 30,
    "High": 55,
    "Critical": 75,
}

TYPE_WEIGHTS = {
    "Medical": 15,
    "Fire": 20,
    "Rescue": 18,
}

RESOURCE_MAP = {
    "Medical": ["Ambulance"],
    "Fire": ["Fire & Rescue"],
    "Rescue": ["Fire & Rescue"],
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/resources", methods=["GET"])
def list_resources():
    conn = get_connection()
    resources = conn.execute("SELECT * FROM resources ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(row) for row in resources])


@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    conn = get_connection()
    incidents = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in incidents])


@app.route("/api/incidents", methods=["POST"])
def create_incident():
    payload = request.get_json(force=True)
    try:
        incident = normalize_incident(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    priority_score = compute_priority_score(incident)
    incident["priority_score"] = priority_score

    conn = get_connection()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents (
                emergency_type,
                severity,
                victim_count,
                latitude,
                longitude,
                time_sensitivity,
                description,
                priority_score,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident["emergency_type"],
                incident["severity"],
                incident["victim_count"],
                incident["latitude"],
                incident["longitude"],
                incident["time_sensitivity"],
                incident["description"],
                priority_score,
                incident["created_at"],
            ),
        )
        incident_id = cursor.lastrowid

    selected = select_best_resource(conn, incident_id, incident)
    dispatch_log = log_dispatch(conn, incident_id, selected)
    conn.close()

    response = {
        "incident_id": incident_id,
        "priority_score": round(priority_score, 2),
        "selected_resource": selected,
        "dispatch": dispatch_log,
    }
    return jsonify(response), 201


@app.route("/api/dispatch/<int:incident_id>", methods=["GET"])
def get_dispatch(incident_id: int):
    conn = get_connection()
    incident = conn.execute(
        "SELECT * FROM incidents WHERE id = ?", (incident_id,)
    ).fetchone()
    if not incident:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    selected = select_best_resource(conn, incident_id, dict(incident))
    dispatch_log = log_dispatch(conn, incident_id, selected)
    conn.close()

    return jsonify(
        {
            "incident_id": incident_id,
            "priority_score": round(incident["priority_score"], 2),
            "selected_resource": selected,
            "dispatch": dispatch_log,
        }
    )


def normalize_incident(payload):
    required = [
        "emergency_type",
        "severity",
        "victim_count",
        "latitude",
        "longitude",
        "time_sensitivity",
    ]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    return {
        "emergency_type": payload["emergency_type"],
        "severity": payload["severity"],
        "victim_count": int(payload["victim_count"]),
        "latitude": float(payload["latitude"]),
        "longitude": float(payload["longitude"]),
        "time_sensitivity": int(payload["time_sensitivity"]),
        "description": payload.get("description", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def compute_priority_score(incident):
    severity_score = SEVERITY_WEIGHTS.get(incident["severity"], 20)
    type_score = TYPE_WEIGHTS.get(incident["emergency_type"], 10)

    victim_factor = min(incident["victim_count"] * 4, 20)
    time_factor = min((60 / max(incident["time_sensitivity"], 1)) * 15, 25)

    base_score = severity_score + type_score + victim_factor + time_factor

    dynamic_scale = 100 / (SEVERITY_WEIGHTS["Critical"] + TYPE_WEIGHTS["Fire"] + 20 + 25)
    return min(base_score * dynamic_scale, 100)


def select_best_resource(conn, incident_id, incident):
    allowed_types = RESOURCE_MAP.get(incident["emergency_type"], [])
    placeholders = ", ".join("?" for _ in allowed_types)
    query = f"""
        SELECT * FROM resources
        WHERE status = 'Available' AND resource_type IN ({placeholders})
    """
    resources = conn.execute(query, allowed_types).fetchall()

    if not resources:
        return {
            "resource_id": None,
            "resource_name": "No available unit",
            "resource_type": None,
            "eta_minutes": None,
        }

    scored = [
        compute_resource_eta(incident_id, incident, dict(resource))
        for resource in resources
    ]
    scored.sort(key=lambda item: item["eta_minutes"])
    return scored[0]


def compute_resource_eta(incident_id, incident, resource):
    distance_km = haversine_km(
        incident["latitude"],
        incident["longitude"],
        resource["latitude"],
        resource["longitude"],
    )
    travel_minutes = (distance_km / resource["avg_speed_kmph"]) * 60
    traffic_multiplier = simulate_traffic_factor(incident_id, resource["id"])
    traffic_delay = travel_minutes * (traffic_multiplier - 1)
    eta_minutes = travel_minutes + traffic_delay + resource["readiness_minutes"]

    return {
        "resource_id": resource["id"],
        "resource_name": resource["name"],
        "resource_type": resource["resource_type"],
        "eta_minutes": round(eta_minutes, 2),
        "distance_km": round(distance_km, 2),
        "traffic_multiplier": round(traffic_multiplier, 2),
    }


def simulate_traffic_factor(incident_id, resource_id):
    seed = incident_id * 31 + resource_id * 17
    normalized = (math.sin(seed) + 1) / 2
    return 1 + normalized * 0.6


def log_dispatch(conn, incident_id, selected):
    if not selected["resource_id"]:
        return {
            "dispatch_status": "Pending",
            "eta_minutes": None,
        }

    created_at = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            """
            INSERT INTO dispatch_logs (
                incident_id,
                resource_id,
                eta_minutes,
                dispatch_status,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                selected["resource_id"],
                selected["eta_minutes"],
                "Dispatched",
                created_at,
            ),
        )

    return {
        "dispatch_status": "Dispatched",
        "eta_minutes": selected["eta_minutes"],
    }


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
