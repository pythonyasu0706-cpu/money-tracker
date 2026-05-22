# app.pyURL
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from services.ocr_service import OCRService
from services.ai_service import ReceiptAIService
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from collections import defaultdict
import traceback
from datetime import datetime, timedelta,timezone,date
import uuid
from collections import defaultdict
from dateutil import parser
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import os

# ================
# インスタンス生成
# ================

load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# DATABASE_URL = os.getenv("DATABASE_URL")
# if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
#     DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
# app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
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
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="draft")
    type = db.Column(db.String(20), default="expense") # "expense" or "income"
    source = db.Column(db.String(10))  # "ocr" or "manual"
    expires_at = db.Column(db.DateTime)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    verification_token = db.Column(db.String(255))
    token_expiry = db.Column(db.DateTime)

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

# ================
# ルーティング
# ================
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/process_receipt', methods=['POST'])
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
    image_url = upload_result["secure_url"]


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
        amount=result.get("total_amount"),
        category="",
        shop_name=result.get("store_name"),
        raw_text=text,
        receipt_date=receipt_date,
        image_path=image_url, #0522変更
        status="draft",
        type="expense",  # ★レシートは固定
        source="ocr",  # ★追加
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify({"redirect": f"/edit/{expense.id}"})

@app.route("/create_expense", methods=["POST"])
def create_expense():
    data = request.json

    receipt_date = None
    if data.get("date"):
        try:
            receipt_date = parser.parse(data.get("date")).date()
        except:
            receipt_date = None

    expense = Transaction(
        amount=data.get("amount"),
        category=data.get("category"),
        shop_name=data.get("store_name"),
        raw_text=data.get("ocr_text", ""),  # 手入力なら空でOK
        receipt_date=receipt_date,
        image_path=data.get("image_path"),  # 手入力はNoneでOK
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


# 編集保存
@app.route("/update_expense", methods=["POST"])
def update_expense():
    data = request.json

    expense_id = data.get("id")
    if not expense_id:
        return jsonify({"error": "missing id"}), 400
            # ★更新
    expense = Transaction.query.get_or_404(expense_id)
    
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
def get_expenses():
    expenses = Transaction.query.order_by(Transaction.created_at.desc()).all()

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
def history():
    expenses = Transaction.query.filter_by(status="confirmed").order_by(desc(Transaction.receipt_date),desc(Transaction.created_at)).all()
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

    return render_template("history.html", grouped_expenses=grouped)
@app.route("/debug")
def debug():
    return "THIS IS CORRECT APP"

# 履歴から編集画面へ
@app.route("/edit/<int:id>")
def edit_expense(id):
    expense = Transaction.query.get_or_404(id)

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
def delete_expense(id):
    expense = Transaction.query.get_or_404(id)

    # 画像も削除したい場合
    if expense.image_path:
        try:
            os.remove(os.path.join("static", expense.image_path))
        except:
            pass

    db.session.delete(expense)
    db.session.commit()

    return jsonify({"status": "deleted"})

# ================
# 分析ページ
# ================
# from datetime import date
# from sqlalchemy import desc
# from collections import defaultdict

# @app.route("/analysis")
# def analysis():
#     # =========================
#     # 全データ取得
#     # =========================
#     expenses = Transaction.query.filter_by(status="confirmed") \
#         .order_by(desc(Transaction.receipt_date), desc(Transaction.created_at)).all()

#     # =========================
#     # 今月だけフィルタ
#     # =========================
#     today = date.today()
#     monthly_expenses = []

#     for e in expenses:
#         d = e.receipt_date or e.created_at.date()

#         if d.year == today.year and d.month == today.month:
#             monthly_expenses.append(e)

#     # =========================
#     # 月ごとグループ（表示用）
#     # =========================
#     grouped = defaultdict(list)

#     for e in monthly_expenses:
#         d = e.receipt_date or e.created_at
#         key = d.strftime("%Y-%m")
#         grouped[key].append(e)

#     # =========================
#     # カテゴリ別（支出のみ）
#     # =========================
#     category_data = {}

#     for e in monthly_expenses:
#         if e.type == "expense":
#             cat = e.category or "未分類"
#             category_data[cat] = category_data.get(cat, 0) + e.amount

#     # =========================
#     # 月間収支合計
#     # =========================
#     monthly_summary = {
#         "expense": 0,
#         "income": 0
#     }

#     for e in monthly_expenses:
#         if e.type == "expense":
#             monthly_summary["expense"] += e.amount
#         else:
#             monthly_summary["income"] += e.amount

#     # =========================
#     # 日別支出（今月のみ）
#     # =========================
#     daily_data = {}

#     for e in monthly_expenses:
#         d = e.receipt_date or e.created_at
#         key = d.strftime("%Y-%m-%d")

#         if key not in daily_data:
#             daily_data[key] = 0

#         if e.type == "expense":
#             daily_data[key] += e.amount

#     return render_template(
#         "analysis.html",
#         grouped_expenses=grouped,
#         daily_data=daily_data,
#         category_data=category_data,
#         monthly_summary=monthly_summary
#     )

@app.route("/analysis")
def analysis():

    expenses = Transaction.query.filter_by(status="confirmed") \
        .order_by(desc(Transaction.receipt_date), desc(Transaction.created_at)).all()

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
        selected_month=selected_month
    )


# ================
# 実行
# ================
if __name__ == "__main__":
    with app.app_context():
        print("DB作成開始")
        db.create_all()
        print("DB作成完了")
        if not scheduler.running:
            scheduler.start() 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
