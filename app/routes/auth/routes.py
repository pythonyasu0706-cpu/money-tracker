# app/routes/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db, login_manager
from app.models.user import User
from app.models.token import EmailVerificationToken
from app.utils.email import send_verification_email,send_password_reset_email
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
import uuid
from datetime import datetime, timedelta, timezone
from app.models.token import PasswordResetToken

auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ================
# ログイン
# ================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("メール認証が完了していません")
                return redirect(url_for("auth.login"))
            
            login_user(user)
            return redirect(url_for("transaction.upload"))

        flash("メールまたはパスワードが違います")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


# ================
# 登録
# ================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    # ======================
    # GET（画面表示）
    # ======================
    if request.method == "GET":
        return render_template("auth/register.html")

    # ======================
    # POST（登録処理）
    # ======================
    email = request.form.get("email", "").lower().strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not email or not password or not password_confirm:
        flash("入力してください")
        return redirect(url_for("auth.register"))

    if password != password_confirm:
        flash("パスワードが一致しません。")
        return redirect(url_for("auth.register"))

    user = User.query.filter_by(email=email).first()

    # ======================
    # 既存ユーザー
    # ======================
    if user:
        if user.is_verified:
            flash("このメールは既に登録されています")
            return redirect(url_for("auth.register"))
    else:
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False
        )
        db.session.add(user)
        db.session.commit()

    # ======================
    # トークン発行（毎回新規）
    # ======================
    EmailVerificationToken.query.filter_by(
        user_id=user.id,
        used=False
    ).update({"used": True})

    token = str(uuid.uuid4())

    db.session.add(EmailVerificationToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    ))

    db.session.commit()

    send_verification_email(user.email, token)

    flash("確認メールを送信しました")
    return redirect(url_for("auth.login"))

# ================
# 認証
# ================
@auth_bp.route("/verify-email/<token>")
def verify_email(token):

    record = EmailVerificationToken.query.filter_by(
        token=token,
        used=False
    ).first()

    if not record:
        return render_template("auth/verify_error.html", message="無効なトークンです")

    now = datetime.now(timezone.utc)

    expires_at = record.expires_at

    # ★ここが修正ポイント（tz統一）
    if expires_at is None:
        return render_template("auth/verify_error.html", message="トークンが不正です")

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return render_template("auth/verify_error.html", message="有効期限切れです")

    user = User.query.get(record.user_id)

    if not user:
        return render_template("auth/verify_error.html", message="ユーザーが存在しません")

    if user.is_verified:
        return render_template("auth/verify_success.html")

    user.is_verified = True
    record.used = True

    db.session.commit()

    return render_template("auth/verify_success.html")
    
# ================
# 未認証ブロック
# ================
@auth_bp.before_request
def check_verification():

    # ① 未ログインは何もしない
    if not current_user.is_authenticated:
        return

    # ② デバッグ表示（ログイン済みのみ）
    print("USER:", current_user.email)
    print("VERIFIED:", current_user.is_verified)

    # ③ 静的ファイルは除外
    if request.blueprint == "static":
        return
    
    # ④ 除外除外ルート
    allowed_routes = {
        "auth.login",
        "auth.register",
        "auth.verify_email",
        "auth.forgot_password",
        "auth.reset_password",
        "static",
        "transaction.landing"    }

    endpoint = request.endpoint
    
    if not endpoint:
        return

    if endpoint in allowed_routes:
        return

    # 未認証ユーザーはブロック
    if endpoint not in allowed_routes:
        if not current_user.is_verified:
            logout_user()
            return redirect(url_for("auth.login"))
        
# ================
# ログアウト
# ================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("landing.html")   

# ================
# パスワードリセット申請（メールアドレス入力）
# ================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email").lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # トークン生成（有効期限1時間など）
            token = str(uuid.uuid4())
            expires = datetime.now(timezone.utc) + timedelta(hours=1)
            
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=expires
            )
            db.session.add(reset_token)
            db.session.commit()
            
            send_password_reset_email(user.email, token)
        
        flash("ご入力いただいたアドレスが登録されている場合、パスワード再設定用のメールを送信しました。", "info")
        return redirect(url_for("auth.login"))
            
    return render_template("auth/forgot_password.html")

# ================
# パスワード再設定実施
# ================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    
    # トークンの有効性チェック
    if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
        flash("リンクが無効か、有効期限が切れています。", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        user = User.query.get(reset_token.user_id)

        # パスワード確認
        if new_password != password_confirm:
            flash("パスワードが一致しません。", "danger")
            return render_template("auth/reset_password.html", token=token)

        # パスワードをハッシュ化して更新
        user.password_hash = generate_password_hash(new_password)
        reset_token.used = True # トークンを使用済みに
        db.session.commit()
        
        flash("パスワードを更新しました。新しいパスワードでログインしてください。", "success")
        return redirect(url_for("auth.login"))
        
    return render_template("auth/reset_password.html", token=token)