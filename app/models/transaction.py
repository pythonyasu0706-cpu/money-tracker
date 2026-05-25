# app/models/transaction.py
from app.extensions import db
from datetime import datetime, timezone

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    category = db.Column(db.String(100))
    shop_name = db.Column(db.String(200))
    raw_text = db.Column(db.Text)
    receipt_date = db.Column(db.Date)
    image_path = db.Column(db.String(300))
    image_public_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="draft")
    type = db.Column(db.String(20), default="expense") # "expense" or "income"
    source = db.Column(db.String(10))  # "ocr" or "manual"
    expires_at = db.Column(db.DateTime)
