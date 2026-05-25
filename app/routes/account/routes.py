# app/routes/account/routes.py
from flask import Blueprint,render_template, redirect, url_for
from flask_login import login_required, current_user, logout_user
from app.models.transaction import Transaction
from app.models.user import User
from app.models.token import EmailVerificationToken
from app.extensions import db


account_bp = Blueprint("account", __name__)

# ================
# アカウントページ
# ================
@account_bp.route("/account")
@login_required
def account():
    return render_template("account/account.html")    

# ================
# アカウント削除
# ================
@account_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    user_id = current_user.id
    # ① 取引削除
    Transaction.query.filter_by(user_id=user_id).delete()
    # トークン削除
    EmailVerificationToken.query.filter_by(user_id=current_user.id).delete()
    # ユーザー削除
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)

    db.session.commit()
    logout_user()
    return redirect(url_for("transaction.landing"))
