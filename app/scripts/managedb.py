# scripts/managedb.py
from app.app import app, db
from app.app import Transaction

with app.app_context():
    Transaction.query.delete()
    db.session.commit()

print("削除完了")
