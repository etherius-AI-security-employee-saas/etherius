import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import desc

from app.ai.insider_threat_ai import calculate_insider_threat_score
from app.database import SessionLocal
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.insider_threat_score import InsiderThreatScore


def _run_once():
    db = SessionLocal()
    try:
        endpoints = db.query(Endpoint).all()
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        for endpoint in endpoints:
            rows = db.query(Event).filter(
                Event.company_id == endpoint.company_id,
                Event.endpoint_id == endpoint.id,
                Event.created_at >= seven_days_ago,
            ).all()
            payload_rows = [
                {
                    "event_type": row.event_type,
                    "payload": row.payload,
                    "risk_score": row.risk_score,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
            previous = db.query(InsiderThreatScore).filter(
                InsiderThreatScore.company_id == endpoint.company_id,
                InsiderThreatScore.endpoint_id == endpoint.id,
            ).order_by(desc(InsiderThreatScore.calculated_at)).first()
            previous_score = int(previous.score) if previous else 0
            result = calculate_insider_threat_score(payload_rows, previous_score=previous_score)
            db.add(
                InsiderThreatScore(
                    company_id=endpoint.company_id,
                    endpoint_id=endpoint.id,
                    score=int(result["score"]),
                    trend=result["trend"],
                    factors=result["factors"],
                    calculated_at=datetime.utcnow(),
                )
            )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def start_insider_scheduler(interval_seconds: int = 3600):
    def loop():
        while True:
            _run_once()
            time.sleep(max(300, int(interval_seconds)))

    thread = threading.Thread(target=loop, daemon=True, name="insider-threat-scheduler")
    thread.start()
    return thread
