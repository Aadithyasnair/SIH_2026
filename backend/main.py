"""
Module F — Backend & Integration.
Exposes the 8 contract endpoints against the REAL repo layout:
  - shared/schemas/records.py     (imported as a package, per conftest.py's sys.path setup)
  - shared/sample_data/*.json     (real pipeline output, replaces placeholders at checkpoints)
  - shared/sample_data/entity_graph.graphml   (Module B's real graph output)

DATABASE_URL env var controls the DB:
  - unset -> sqlite:///./app.db  (fast local dev, no setup needed)
  - set to postgresql://sih_user:sih_password@postgres:5432/sih_bitcoin -> real Postgres,
    used inside docker-compose (matches the team's existing service).
"""
import json
import os
import uuid
from contextlib import contextmanager

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from shared.schemas.records import Alert, Cluster

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
SAMPLE_DATA = os.path.join(os.path.dirname(__file__), "..", "shared", "sample_data")
ALERTS_FILE = os.path.join(SAMPLE_DATA, "alerts.json")
CLUSTERS_FILE = os.path.join(SAMPLE_DATA, "clusters.json")
GRAPH_FILE = os.path.join(SAMPLE_DATA, "entity_graph.graphml")       # Module B's real output
LIVE_FEED_FILE = os.path.join(SAMPLE_DATA, "network_events.json")    # Module A's real output

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

app = FastAPI(title="SIH26146 Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

JOBS = {}          # in-memory job tracking — fine for a 2-day demo, not a queue
_GRAPH_CACHE = None  # loaded once, GraphML parsing is not cheap at 2MB+


@contextmanager
def get_db():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                txid TEXT,
                involved_addresses TEXT,
                risk_score REAL,
                anomaly_score REAL,
                propagated_risk_score REAL,
                pattern_type TEXT,
                cluster_id TEXT,
                flags TEXT,
                explanation TEXT,
                timestamp TEXT,
                geo_summary TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clusters (
                cluster_id TEXT PRIMARY KEY,
                label TEXT,
                member_addresses TEXT,
                member_count INTEGER,
                avg_risk_score REAL,
                description TEXT,
                clustering_method TEXT
            )
        """))
        conn.commit()


def load_alerts_from_json():
    if not os.path.exists(ALERTS_FILE):
        return 0
    with open(ALERTS_FILE) as f:
        raw_alerts = json.load(f)
    count = 0
    with get_db() as conn:
        for raw in raw_alerts:
            a = Alert(**raw)  # validates against the shared schema — fails loudly if wrong
            conn.execute(
                text("""INSERT INTO alerts
                   (alert_id, txid, involved_addresses, risk_score, anomaly_score,
                    propagated_risk_score, pattern_type, cluster_id, flags, explanation,
                    timestamp, geo_summary)
                   VALUES (:alert_id,:txid,:involved_addresses,:risk_score,:anomaly_score,
                    :propagated_risk_score,:pattern_type,:cluster_id,:flags,:explanation,
                    :timestamp,:geo_summary)
                   ON CONFLICT (alert_id) DO UPDATE SET
                    txid = EXCLUDED.txid,
                    involved_addresses = EXCLUDED.involved_addresses,
                    risk_score = EXCLUDED.risk_score,
                    anomaly_score = EXCLUDED.anomaly_score,
                    propagated_risk_score = EXCLUDED.propagated_risk_score,
                    pattern_type = EXCLUDED.pattern_type,
                    cluster_id = EXCLUDED.cluster_id,
                    flags = EXCLUDED.flags,
                    explanation = EXCLUDED.explanation,
                    timestamp = EXCLUDED.timestamp,
                    geo_summary = EXCLUDED.geo_summary"""),
                {
                    "alert_id": a.alert_id, "txid": a.txid,
                    "involved_addresses": json.dumps(a.involved_addresses),
                    "risk_score": a.risk_score, "anomaly_score": a.anomaly_score,
                    "propagated_risk_score": a.propagated_risk_score,
                    "pattern_type": a.pattern_type, "cluster_id": a.cluster_id,
                    "flags": json.dumps(a.flags), "explanation": a.explanation,
                    "timestamp": a.timestamp, "geo_summary": a.geo_summary,
                },
            )
            count += 1
        conn.commit()
    return count


def load_clusters_from_json():
    if not os.path.exists(CLUSTERS_FILE):
        return 0
    with open(CLUSTERS_FILE) as f:
        raw_clusters = json.load(f)
    count = 0
    with get_db() as conn:
        for raw in raw_clusters:
            c = Cluster(**raw)
            conn.execute(
                text("""INSERT INTO clusters
                   (cluster_id, label, member_addresses, member_count, avg_risk_score,
                    description, clustering_method)
                   VALUES (:cluster_id,:label,:member_addresses,:member_count,:avg_risk_score,
                    :description,:clustering_method)
                   ON CONFLICT (cluster_id) DO UPDATE SET
                    label = EXCLUDED.label,
                    member_addresses = EXCLUDED.member_addresses,
                    member_count = EXCLUDED.member_count,
                    avg_risk_score = EXCLUDED.avg_risk_score,
                    description = EXCLUDED.description,
                    clustering_method = EXCLUDED.clustering_method"""),
                {
                    "cluster_id": c.cluster_id, "label": c.label,
                    "member_addresses": json.dumps(c.member_addresses),
                    "member_count": c.member_count, "avg_risk_score": c.avg_risk_score,
                    "description": c.description, "clustering_method": c.clustering_method,
                },
            )
            count += 1
        # Synchronize avg_risk_score from associated alerts using severity-preserving weighting
        conn.execute(
            text("""
                UPDATE clusters
                SET avg_risk_score = COALESCE((
                    SELECT ROUND(CAST(0.75 * MAX(alerts.risk_score) + 0.25 * AVG(alerts.risk_score) AS numeric), 4)
                    FROM alerts
                    WHERE alerts.cluster_id = clusters.cluster_id
                ), clusters.avg_risk_score)
                WHERE EXISTS (
                    SELECT 1 FROM alerts WHERE alerts.cluster_id = clusters.cluster_id
                )
            """)
        )
        # Ensure clusters touching detected patterns are labeled and scored as high-risk
        conn.execute(
            text("""
                UPDATE clusters
                SET avg_risk_score = GREATEST(avg_risk_score, 0.75),
                    label = CASE
                        WHEN label = 'Multi-Wallet Entity' THEN 'High-Risk Peeling & Laundering Entity'
                        WHEN label = 'Consolidation Vault Entity' THEN 'High-Risk Layering Vault'
                        ELSE label
                    END
                WHERE EXISTS (
                    SELECT 1 FROM alerts 
                    WHERE alerts.cluster_id = clusters.cluster_id 
                    AND (alerts.pattern_type IN ('peeling_chain', 'coinjoin_mixing') OR alerts.flags::text LIKE '%peel%' OR alerts.flags::text LIKE '%layer%')
                )
            """)
        )
        conn.commit()
    return count


def row_to_alert_dict(row):
    return {
        "alert_id": row.alert_id, "txid": row.txid,
        "involved_addresses": json.loads(row.involved_addresses),
        "risk_score": row.risk_score, "anomaly_score": row.anomaly_score,
        "propagated_risk_score": row.propagated_risk_score,
        "pattern_type": row.pattern_type, "cluster_id": row.cluster_id,
        "flags": json.loads(row.flags), "explanation": row.explanation,
        "timestamp": row.timestamp, "geo_summary": row.geo_summary,
    }


def row_to_cluster_dict(row):
    return {
        "cluster_id": row.cluster_id, "label": row.label,
        "member_addresses": json.loads(row.member_addresses),
        "member_count": row.member_count, "avg_risk_score": row.avg_risk_score,
        "description": row.description, "clustering_method": row.clustering_method,
    }


def get_graph():
    global _GRAPH_CACHE
    if _GRAPH_CACHE is None and os.path.exists(GRAPH_FILE):
        _GRAPH_CACHE = nx.read_graphml(GRAPH_FILE)
    return _GRAPH_CACHE


@app.on_event("startup")
def startup():
    init_db()
    n_alerts = load_alerts_from_json()
    n_clusters = load_clusters_from_json()
    print(f"Loaded {n_alerts} alerts, {n_clusters} clusters")


@app.get("/api/alerts")
def list_alerts(risk_min: float = 0.0, limit: int = 50, offset: int = 0):
    with get_db() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM alerts WHERE risk_score >= :r"), {"r": risk_min}
        ).scalar()
        rows = conn.execute(
            text("SELECT * FROM alerts WHERE risk_score >= :r ORDER BY risk_score DESC LIMIT :l OFFSET :o"),
            {"r": risk_min, "l": limit, "o": offset},
        ).fetchall()
    return {"alerts": [row_to_alert_dict(r) for r in rows], "total": total}


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: str):
    with get_db() as conn:
        row = conn.execute(text("SELECT * FROM alerts WHERE alert_id = :id"), {"id": alert_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return row_to_alert_dict(row)


@app.get("/api/clusters")
def list_clusters():
    with get_db() as conn:
        rows = conn.execute(text("SELECT * FROM clusters ORDER BY avg_risk_score DESC")).fetchall()
    return {"clusters": [row_to_cluster_dict(r) for r in rows]}


@app.get("/api/clusters/{cluster_id}")
def get_cluster(cluster_id: str):
    with get_db() as conn:
        row = conn.execute(text("SELECT * FROM clusters WHERE cluster_id = :id"), {"id": cluster_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="cluster not found")
    return row_to_cluster_dict(row)


@app.get("/api/graph/{node_id}")
def get_graph_endpoint(node_id: str, depth: int = 2):
    """Real subgraph extraction from Module B's GraphML output using an ego graph."""
    graph = get_graph()
    if graph is None or node_id not in graph:
        return {"nodes": [{"id": node_id, "type": "unknown", "label": node_id}], "edges": []}

    sub = nx.ego_graph(graph, node_id, radius=depth)
    nodes = [
        {"id": n, "type": sub.nodes[n].get("type", "unknown"), "label": sub.nodes[n].get("label", n)}
        for n in sub.nodes
    ]
    edges = []
    for edge in sub.edges:
        u = edge[0]
        v = edge[1]
        edge_data = sub.get_edge_data(*edge) or {}
        confidence = float(edge_data.get("confidence", 0.0))
        edges.append({"source": u, "target": v, "confidence": confidence})
    return {"nodes": nodes, "edges": edges}


@app.get("/api/live-feed")
def live_feed(speed: float = 1.0, from_ts: str = None, to_ts: str = None):
    """Ordered network events with geo coords for the frontend's globe playback."""
    if not os.path.exists(LIVE_FEED_FILE):
        return {"events": []}
    with open(LIVE_FEED_FILE) as f:
        events = json.load(f)
    if from_ts:
        events = [e for e in events if e["timestamp"] >= from_ts]
    if to_ts:
        events = [e for e in events if e["timestamp"] <= to_ts]
    events.sort(key=lambda e: e["timestamp"])
    return {"events": events, "speed": speed}


from fastapi import BackgroundTasks
from backend.pipeline import run_full_pipeline


def _execute_pipeline_job(job_id: str):
    try:
        def update_progress(progress: float, stage: str):
            if job_id in JOBS:
                JOBS[job_id]["progress"] = progress
                JOBS[job_id]["stage"] = stage

        result = run_full_pipeline(progress_callback=update_progress)
        n_alerts = load_alerts_from_json()
        n_clusters = load_clusters_from_json()
        global _GRAPH_CACHE
        _GRAPH_CACHE = None  # refresh graph cache
        JOBS[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "stage": "Pipeline completed successfully",
            "alerts_loaded": n_alerts,
            "clusters_loaded": n_clusters,
        })
    except Exception as e:
        JOBS[job_id].update({
            "status": "failed",
            "error": str(e),
            "stage": f"Error: {e}",
        })


@app.post("/api/ingest")
def trigger_ingest(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "running",
        "progress": 0.0,
        "stage": "Initializing pipeline execution...",
    }
    background_tasks.add_task(_execute_pipeline_job, job_id)
    return {"job_id": job_id, "status": "running"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/")
def health():
    return {"status": "ok", "database": DATABASE_URL.split("://")[0]}
