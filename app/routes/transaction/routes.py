# app/routes/transaction/routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
import cloudinary.uploader
import traceback
from datetime import datetime, timedelta, timezone
from dateutil import parser
from sqlalchemy import desc
from collections import defaultdict
from app.extensions import db
from app.models.transaction import Transaction
from app.utils.color_map import get_color_map

transaction_bp = Blueprint("transaction", __name__)

@transaction_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("transaction.upload"))
    return render_template("landing.html")

@transaction_bp.route("/upload")
@login_required
def upload():
    return render_template("transaction/upload.html")

@transaction_bp.route('/process_receipt', methods=['POST'])
@login_required
def process_receipt():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # ファイル取得
    image = request.files['image']

    # クラウド
    upload_result = cloudinary.uploader.upload(image)

    image_url = upload_result["secure_url"] #表示用URL
    public_id = upload_result["public_id"] #削除キー

    # text = current_app.ocr.extract_text(image_url)
    # result = current_app.ai.parse(text)

    # OCR処理
    try:
        text = current_app.ocr.extract_text(image_url)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    if text == "OCRエラー":
        return jsonify({"error": "OCR failed"}), 500

    result = current_app.ai.parse(text)

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

    return jsonify({
        "status": "ok",
        "id": expense.id
    })

# ================
# 経費登録（手入力）
# ================
@transaction_bp.route("/create_expense", methods=["POST"])
@login_required
def create_expense():
    data = request.json

    # 日付
    receipt_date = None
    if data.get("date"):
        try:
            receipt_date = parser.parse(data.get("date")).date()
        except:
            receipt_date = None

    # 金額
    amount_raw = data.get("amount", "")

    if amount_raw == "":
        return jsonify({"error": "金額を入力してください"}), 400

    try:
        amount = int(amount_raw)
    except ValueError:
        return jsonify({"error": "金額は数字で入力してください"}), 400

    # 保存
    expense = Transaction(
        user_id=current_user.id,
        amount=amount,
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
@transaction_bp.route("/update_expense", methods=["POST"])
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
@transaction_bp.route("/expenses", methods=["GET"])
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
@transaction_bp.route("/history")
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

    return render_template("transaction/history.html",
                        color_map=get_color_map(),
                        grouped_expenses=grouped)

@transaction_bp.route("/debug")
def debug():
    return "THIS IS CORRECT APP"

# 履歴から編集画面へ
@transaction_bp.route("/edit/<int:id>")
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

        return render_template("transaction/ocr_edit.html", data=data)

    # =====================
    # 手入力ルート
    # =====================
    else:
        return render_template("transaction/manual_edit.html", data=data)
@transaction_bp.route("/delete_expense/<int:id>", methods=["DELETE"])
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
