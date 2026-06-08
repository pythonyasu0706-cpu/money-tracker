# app/modeles/user.py
from app.extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    # ==========================================
    #  追記：芋づる式に削除（カスケード削除）するリレーションシップ
    # ==========================================
    # パスワードリセットトークンとの連動設定
    password_reset_tokens = db.relationship(
        "PasswordResetToken", 
        backref="user", 
        cascade="all, delete-orphan"
    )
    
    # メール認証トークンとの連動設定
    email_verification_tokens = db.relationship(
        "EmailVerificationToken", 
        backref="user", 
        cascade="all, delete-orphan"
    )

    #  追記：家計簿データ（Transaction）も連動して削除する設定を追加！
    transactions = db.relationship(
        "Transaction", 
        backref="user", 
        cascade="all, delete-orphan"
    )