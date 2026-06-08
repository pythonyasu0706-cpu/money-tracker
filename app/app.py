# app/app.py
from flask import Flask, redirect, url_for
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import resend
import cloudinary
from app.utils.scheduler import init_scheduler

from app.extensions import db, login_manager, migrate
from app.services.ocr_service import OCRService
from app.services.ai_service import ReceiptAIService

from app.routes.account.routes import account_bp
from app.routes.auth.routes import auth_bp
from app.routes.analysis.routes import analysis_bp
from app.routes.transaction.routes import transaction_bp
from app.models.user import User
from app.models.transaction import Transaction
from app.models.token import EmailVerificationToken, PasswordResetToken

load_dotenv()

# blueprint登録
def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(transaction_bp, url_prefix="/transaction")
    app.register_blueprint(analysis_bp, url_prefix="/analysis")

# 初期化
def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

def init_services(app):
    app.ocr = OCRService()
    app.ai = ReceiptAIService()

def create_app():
    app = Flask(__name__)

    # 設定
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

    # 環境変数から取得（ローカル開発用にSQLiteをフォールバックに指定しておくと便利です）
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

    # Neonの 'postgres://' を SQLAlchemy 用の 'postgresql://' に変換
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 警告を非表示にするため推奨

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    resend.api_key = os.getenv("RESEND_API_KEY")

    init_extensions(app)
    register_blueprints(app)
    init_scheduler(app)
    init_services(app)

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )

    app.ocr = OCRService()
    app.ai = ReceiptAIService()


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ================
    # ルーティング
    # ================
    @app.route("/")
    def root():
        return redirect(url_for("transaction.landing"))

    return app

app = create_app()



if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))