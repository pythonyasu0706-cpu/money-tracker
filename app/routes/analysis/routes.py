# app/routes/nalysis/routes.py
from sqlalchemy import desc
from datetime import date
from flask import request
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.extensions import db
from app.models.transaction import Transaction
from app.utils.color_map import get_color_map

analysis_bp = Blueprint("analysis", __name__)

# ================
# 分析ページ
# ================
@analysis_bp.route("/analysis")
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
        "transaction/analysis.html",
        grouped_expenses=grouped,
        daily_data=daily_data,
        category_data=category_data,
        monthly_summary=monthly_summary,
        months=months,
        selected_month=selected_month,
        color_map=get_color_map()
    )
