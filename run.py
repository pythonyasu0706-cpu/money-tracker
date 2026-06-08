# run.py
import os
from app.app import create_app

# アプリケーションファクトリ(create_app)を呼び出してappインスタンスを生成
app = create_app()

if __name__ == "__main__":
    # Renderなどのデプロイ環境とローカル環境の両方に対応できるように設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)