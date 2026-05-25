# scripts/delete_user.py
from app.app import app, db, User

email = "python.yasu0706@gmail.com"

with app.app_context():
    user = User.query.filter_by(email=email).first()

    if user:
        db.session.delete(user)
        db.session.commit()
        print("削除完了")
    else:
        print("ユーザーいない")