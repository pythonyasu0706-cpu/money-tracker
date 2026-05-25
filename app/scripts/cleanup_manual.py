# scripts/cleanup_manual.py
from app.app import app, db, Transaction
from datetime import datetime, timezone

with app.app_context():
    now = datetime.now(timezone.utc)

    Transaction.query.filter(
        Transaction.status == "draft",
        Transaction.expires_at < now
    ).delete()

    db.session.commit()