# app/utils/email.py
import os
import resend
from flask import request

def get_base_url():
    """現在がデバッグ（ローカル）環境か本番環境かでURLを自動で切り替える関数"""
    # 1. もし現在Webリクエストの最中であれば、今アクセスされているURLのドメインを自動取得する（一番確実）
    try:
        # これにより、ローカルなら http://127.0.0.1:5000/ 、本番なら https://yasumasu.com/ が自動で取れます
        return request.host_url.rstrip('/')
    except RuntimeError:
        # バックグラウンド処理など、Flaskのリクエスト外から呼ばれた場合のフォールバック
        if os.getenv("FLASK_DEBUG") == "1" or os.getenv("FLASK_ENV") == "development":
            return "http://127.0.0.1:5000"
        return os.getenv("BASE_URL", "https://yasumasu.com").rstrip('/')

# ====================
# メール認証用送信関数
# ====================
def send_verification_email(email, token):

    BASE_URL = get_base_url()
    verify_url = f"{BASE_URL}/auth/verify-email/{token}"

    try:
        result = resend.Emails.send({
            "from": "no-reply@yasumasu.com",
            "to": email,
            "subject": "メール認証してください",
            "html": f"""
                <p>登録ありがとうございます</p>
                <p>以下をクリックしてください</p>
                <a href="{verify_url}">メール認証する</a>
            """
        })

        print(result)

    except Exception as e:
        print("Email send failed:", str(e))

def send_password_reset_email(email, token):
    BASE_URL = get_base_url()
    reset_url = f"{BASE_URL}/auth/reset-password/{token}"

    # Resend等を使用したメール送信ロジック
    # (既存のメール送信コードを流用してください)
    try:
        result = resend.Emails.send({
            "from": "no-reply@yasumasu.com",
            "to": email,
            "subject": "パスワード再設定",
            "html": f"""
                <p>パスワード再設定依頼を受け付けました</p>
                <p>以下をクリックしてください</p>
                <a href="{reset_url}">パスワードを再設定する</a>
            """
        })
        print(result)
    except Exception as e:
        print("Password reset email send failed:", str(e))

    print(f"Reset URL: {reset_url}") # 開発用ログ