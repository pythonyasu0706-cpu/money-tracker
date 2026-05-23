# app.pyURL
from flask import Flask, render_template, request, jsonify, session, redirect, url_for,flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
# from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from services.ocr_service import OCRService
from services.ai_service import ReceiptAIService
from collections import defaultdict
import traceback
from datetime import datetime, timedelta,timezone,date
import uuid
import resend
from collections import defaultdict
from dateutil import parser
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import os


load_dotenv()

# ================
# インスタンス生成
# ================
app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# DATABASE_URL = os.getenv("DATABASE_URL")
# if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
#     DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
# app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
resend.api_key = os.environ.get("RESEND_API_KEY")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def get_services():
    return {
        "ocr": OCRService(),
        "ai": ReceiptAIService()
    }

services = get_services()
ocr = services["ocr"]
ai = services["ai"]

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # verification_token = db.Column(db.String(255), index=True, unique=True)
    # token_expiry = db.Column(db.DateTime)

class EmailVerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(255), unique=True, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# uploadsディレクトリが存在しない場合は作成
# os.makedirs("static/uploads", exist_ok=True)

def cleanup_drafts():
    with app.app_context():
        now = datetime.now(timezone.utc)

        Transaction.query.filter(
            Transaction.status == "draft",
            Transaction.expires_at < now
        ).delete()

        db.session.commit()
        print("draft cleaned")

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_drafts, trigger="interval", hours=1)
scheduler.start()

# メール送信関数
def send_verification_email(email, token):

    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
    verify_url = f"{BASE_URL}/verify-email/{token}"

    resend.Emails.send({
        "from": "no-reply@yasumasu.com",
        "to": email,
        "subject": "メール認証してください",
        "html": f"""
            <p>登録ありがとうございます</p>
            <p>以下をクリックしてください</p>
            <a href="{verify_url}">メール認証する</a>
        """
    })

# カラーマップ
def get_color_map():
    return {
        "食費": "bg-amber-300 text-on-tertiary-fixed-variant",
        "交通費": "bg-purple-300 text-on-secondary-fixed-variant",
        "消耗品費": "bg-tertiary-fixed text-on-surface-variant",
        "交際費": "bg-primary-fixed text-on-primary-fixed-variant",
        "通信費": "bg-secondary-container text-on-secondary-container",
        "水道光熱費": "bg-tertiary-container text-on-tertiary-container",
        "地代家賃": "bg-primary-container text-on-primary-container",
        "広告宣伝費": "bg-secondary-fixed text-on-secondary-fixed-variant",
        "会議費": "bg-tertiary-fixed text-on-tertiary-fixed-variant",
        "雑費": "bg-surface-container-high text-on-surface-variant",
        "給与": "bg-red-300 text-on-primary-fixed-variant"
    }

# ================
# ルーティング
# ================

@app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("upload"))
    return render_template("landing.html")

@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html")

@app.route('/process_receipt', methods=['POST'])
@login_required
def process_receipt():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # ファイル取得
    image = request.files['image']


    # ファイル名を安全な形式に変換
    # original_filename = secure_filename(image.filename)
    # filename = f"{uuid.uuid4()}_{original_filename}" # ファイル名の衝突を避けるためにUUIDを追加
    # db_path = f"uploads/{filename}"

    # ローカルのみ
    # ★実ファイル保存
    # save_path = os.path.join("static", db_path)
    # image.save(save_path)
    
    # クラウド
    upload_result = cloudinary.uploader.upload(image)

    image_url = upload_result["secure_url"] #表示用URL
    public_id = upload_result["public_id"] #削除キー

    # OCR処理
    try:
        text = ocr.extract_text(image_url)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    if text == "OCRエラー":
        return jsonify({"error": "OCR failed"}), 500

    result = ai.parse(text)

    # OCR結果から日付があれば使う（AI側）
    raw_date = result.get("date")

    receipt_date = None
    if raw_date:
        try:
            receipt_date = parser.parse(raw_date).date()
        except:
            receipt_date = None

    # 新規作成(OCRボタンを押すとここで初めてDB保存)
    expense = Transaction(
        user_id=current_user.id,
        amount=result.get("total_amount"),
        category="",
        shop_name=result.get("store_name"),
        raw_text=text,
        receipt_date=receipt_date,
        image_path=image_url, #0522変更
        image_public_id=public_id, #0522変更
        status="draft",
        type="expense",  # ★レシートは固定
        source="ocr",  # ★追加
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify({"redirect": f"/edit/{expense.id}"})

# ================
# 登録
# ================
@app.route("/register", methods=["GET", "POST"])
def register():

    # ======================
    # GET（画面表示）
    # ======================
    if request.method == "GET":
        return render_template("register.html")

    # ======================
    # POST（登録処理）
    # ======================
    email = request.form.get("email", "").lower().strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("入力してください")
        return redirect(url_for("register"))

    user = User.query.filter_by(email=email).first()

    # ======================
    # 既存ユーザー
    # ======================
    if user:
        if user.is_verified:
            flash("このメールは既に登録されています")
            return redirect(url_for("register"))
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
    return redirect(url_for("login"))

# ================
# 認証
# ================
@app.route("/verify-email/<token>")
def verify_email(token):

    record = EmailVerificationToken.query.filter_by(
        token=token,
        used=False
    ).first()

    if not record:
        return render_template("verify_error.html", message="無効なトークンです")

    now = datetime.now(timezone.utc)

    expires_at = record.expires_at

    # ★ここが修正ポイント（tz統一）
    if expires_at is None:
        return render_template("verify_error.html", message="トークンが不正です")

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return render_template("verify_error.html", message="有効期限切れです")

    user = User.query.get(record.user_id)

    if not user:
        return render_template("verify_error.html", message="ユーザーが存在しません")

    if user.is_verified:
        return render_template("verify_success.html")

    user.is_verified = True
    record.used = True

    db.session.commit()

    return render_template("verify_success.html")
    
# ================
# 未認証ブロック
# ================
@app.before_request
def check_verification():

    if not current_user.is_authenticated:
        return

    # 除外ルート
    allowed_routes = {
        "login",
        "register",
        "verify_email",
        "static"
    }

    endpoint = request.endpoint

    if endpoint is None:
        return

    # staticは常にOK
    if request.blueprint == "static":
        return

    # 未認証ユーザーはブロック
    if endpoint not in allowed_routes:
        if not current_user.is_verified:
            logout_user()
            return redirect(url_for("login"))
        
# ================
# ログイン
# ================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("メール認証が完了していません")
                return redirect(url_for("login"))
            
            login_user(user)
            return redirect(url_for("upload"))

        flash("メールまたはパスワードが違います")
        return redirect(url_for("login"))

    return render_template("login.html")

# ================
# ログアウト
# ================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("landing.html")   

# ================
# アカウントページ
# ================
@app.route("/account")
@login_required
def account():
    return render_template("account.html")    

# ================
# アカウント削除
# ================
@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    logout_user()
    return redirect(url_for("landing"))

# ================
# 手入力
# ================
@app.route("/create_expense", methods=["POST"])
@login_required
def create_expense():
    data = request.json

    receipt_date = None
    if data.get("date"):
        try:
            receipt_date = parser.parse(data.get("date")).date()
        except:
            receipt_date = None

    expense = Transaction(
        user_id=current_user.id,
        amount=data.get("amount"),
        category=data.get("category"),
        shop_name=data.get("store_name"),
        raw_text=data.get("ocr_text", ""),  # 手入力なら空でOK
        receipt_date=receipt_date,
        image_path=data.get("image_path"),  # 手入力はNoneでOK
        image_public_id=None, #0522変更
        status="confirmed",
        type=data.get("type", "expense"),
        source="manual",  # ★追加
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify({
        "status": "ok",
        "id": expense.id
    })


# ================
# OCR後編集
# ================
@app.route("/update_expense", methods=["POST"])
@login_required
def update_expense():
    data = request.json

    expense_id = data.get("id")
    if not expense_id:
        return jsonify({"error": "missing id"}), 400
            # ★更新
    expense = Transaction.query.filter_by(
        id=expense_id,
        user_id=current_user.id
    ).first_or_404()
    
    receipt_date = None
    if data.get("date"):
        try:
            receipt_date = parser.parse(data.get("date")).date()
        except:
            receipt_date = None

    print(data)  # ← とりあえず確認


    expense.amount = data.get("amount")
    expense.category = data.get("category")
    expense.shop_name = data.get("store_name")
    expense.receipt_date = receipt_date
    expense.status = "confirmed"


    db.session.commit()
    return jsonify({"status": "ok"})

# TODO: 認証機能実装後、ユーザーごとの履歴表示にする
@app.route("/expenses", methods=["GET"])
@login_required
def get_expenses():
    expenses = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).all()

    result = []
    for e in expenses:
        result.append({
            "id": e.id,
            "amount": e.amount,
            "category": e.category,
            "shop_name": e.shop_name,
            "raw_text": e.raw_text,
            "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result)

# TODO: 認証機能実装後、ユーザーごとの履歴表示にする
@app.route("/history")
@login_required
def history():
    expenses = Transaction.query.filter_by(
        status="confirmed",
        user_id=current_user.id
        ).order_by(
            desc(Transaction.receipt_date),
            desc(Transaction.created_at)
        ).all()
    grouped = defaultdict(list)

    for e in expenses:
        date = e.receipt_date or e.created_at

        if date:
            key = date.strftime("%Y年%m月")
        else:
            key = "日付不明"

        grouped[key].append(e)
    
    # ★ここ追加（これだけ）
    grouped = dict(
        sorted(grouped.items(), key=lambda x: x[0], reverse=True)
    )

    return render_template("history.html",
                        color_map=get_color_map(),
                        grouped_expenses=grouped)

@app.route("/debug")
def debug():
    return "THIS IS CORRECT APP"

# 履歴から編集画面へ
@app.route("/edit/<int:id>")
@login_required
def edit_expense(id):
    expense = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    # 共通データ
    data = {
        "id": expense.id,
        "status": expense.status,
        "category": expense.category,
        "type": expense.type,
        "store_name": expense.shop_name,
        "date": expense.receipt_date.strftime("%Y-%m-%d") if expense.receipt_date else "",
        "amount": expense.amount
    }

    # =====================
    # OCRルート
    # =====================
    if expense.source == "ocr":

        image_url = None
        if expense.image_path:
            image_url = expense.image_path

        data.update({
            "image_url": image_url,
            "ocr_text": expense.raw_text or "（OCRなし）",
            "result": {
                "store_name": expense.shop_name,
                "date": data["date"],
                "total_amount": expense.amount
            },
            "categories": ai.parse(expense.raw_text).get("categories", [])
        })

        return render_template("ocr_edit.html", data=data)

    # =====================
    # 手入力ルート
    # =====================
    else:
        return render_template("manual_edit.html", data=data)
@app.route("/delete_expense/<int:id>", methods=["DELETE"])
@login_required
def delete_expense(id):
    expense = Transaction.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    # 画像も削除したい場合
    if expense.image_public_id:
        try:
            cloudinary.uploader.destroy(expense.image_public_id)
        except:
            pass

    db.session.delete(expense)
    db.session.commit()

    return jsonify({"status": "deleted"})

# ================
# 分析ページ
# ================
@app.route("/analysis")
@login_required
def analysis():

    expenses = Transaction.query.filter_by(
        status="confirmed",
        user_id=current_user.id
    ).order_by(
        desc(Transaction.receipt_date), 
        desc(Transaction.created_at)
    ).all()

    # =========================
    # 月選択
    # =========================
    selected_month = request.args.get("month")
    today = date.today()

    if selected_month:
        year, month = map(int, selected_month.split("-"))
    else:
        year, month = today.year, today.month
        selected_month = f"{year}-{month:02d}"

    # =========================
    # 月フィルタ
    # =========================
    monthly_expenses = []

    for e in expenses:
        d = e.receipt_date or e.created_at.date()
        if d.year == year and d.month == month:
            monthly_expenses.append(e)

    # =========================
    # 月リスト（selectbox用）
    # =========================
    months = sorted({
        (e.receipt_date or e.created_at.date()).strftime("%Y-%m")
        for e in expenses
    }, reverse=True)

    # =========================
    # グルーピング（表示用）
    # =========================
    grouped = {selected_month: monthly_expenses}

    # =========================
    # カテゴリ集計
    # =========================
    category_data = {}

    for e in monthly_expenses:
        if e.type == "expense":
            cat = e.category or "未分類"
            category_data[cat] = category_data.get(cat, 0) + e.amount

    # =========================
    # 収支
    # =========================
    monthly_summary = {"expense": 0, "income": 0}

    for e in monthly_expenses:
        if e.type == "expense":
            monthly_summary["expense"] += e.amount
        else:
            monthly_summary["income"] += e.amount

    # =========================
    # 日別
    # =========================
    daily_data = {}

    for e in monthly_expenses:
        d = e.receipt_date or e.created_at
        key = d.strftime("%Y-%m-%d")

        if e.type == "expense":
            daily_data[key] = daily_data.get(key, 0) + e.amount

    return render_template(
        "analysis.html",
        grouped_expenses=grouped,
        daily_data=daily_data,
        category_data=category_data,
        monthly_summary=monthly_summary,
        months=months,
        selected_month=selected_month,
        color_map=get_color_map()
    )


# ================
# 実行
# ================
if __name__ == "__main__":
    with app.app_context():
        # print("DB作成開始")
        # db.create_all()
        # print("DB作成完了")
        if not scheduler.running:
            scheduler.start() 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
