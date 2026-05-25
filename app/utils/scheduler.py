# app/utils/scheduler.py
# utils/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from app.extensions import db
from app.models.transaction import Transaction

def cleanup_drafts(app):
    with app.app_context():
        now = datetime.now(timezone.utc)

        Transaction.query.filter(
            Transaction.status == "draft",
            Transaction.expires_at < now
        ).delete()

        db.session.commit()
        print("draft cleaned")

# scheduler = BackgroundScheduler()
# scheduler.add_job(func=cleanup_drafts, trigger="interval", hours=1)
# scheduler.start()
# app.scheduler = scheduler


def init_scheduler(app):
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        func=lambda: cleanup_drafts(app),
        trigger="interval",
        hours=1
    )

    scheduler.start()
    app.scheduler = scheduler