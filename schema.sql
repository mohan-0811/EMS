CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emergency_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    victim_count INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    time_sensitivity INTEGER NOT NULL,
    description TEXT,
    priority_score REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT NOT NULL,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    readiness_minutes INTEGER NOT NULL,
    avg_speed_kmph REAL NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispatch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    eta_minutes REAL NOT NULL,
    dispatch_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (incident_id) REFERENCES incidents(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);
