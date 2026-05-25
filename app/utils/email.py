# app/utils/email.py
import os
import resend

# メール送信関数
def send_verification_email(email, token):

    BASE_URL = os.getenv("BASE_URL")
    if not BASE_URL:
        BASE_URL = "http://localhost:5000"
        
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