# services/ai_service.py
from openai import OpenAI
from dotenv import load_dotenv

import os
import json

load_dotenv()

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )

class ReceiptAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

class ReceiptAIService:
    def __init__(self):
        self.client = client

    def parse(self, text):
        # ここでテキストを解析して、必要な情報を抽出するロジックを実装します。
        # 例えば、日付、店舗名、合計金額などを抽出することができます。
        # これは単純な例であり、実際のレシートのフォーマットに応じて調整が必要です。

        response = self.client.chat.completions.create( #.chat.completions.create()は、OpenAIのAPIを呼び出して、チャット形式の応答を生成するためのメソッド。completion = 「続きを完成させる」create() = APIリクエストを送信して、応答を生成するための関数。
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
    あなたはレシート解析AIです。
    以下の情報を抽出してJSONで返してください：

    - store_name（店舗名）
    - date（日付）
    - total_amount（合計金額）
    - categories（勘定科目の候補を3つ、日本語で）

    勘定科目は以下から選んでください：
    消耗品費、旅費交通費、交際費、通信費、水道光熱費、雑費、食費

    必ずJSONだけ返してください。
    """
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        # return json.loads(response.choices[0].message.content)
        content = response.choices[0].message.content
        print("AI RESPONSE:", content)  #AIからの応答をログに出力して確認
        content = content.replace("```json", "").replace("```", "").strip() #AIがJSONをコードブロックで返す場合に備えて、コードブロックのマーカーを削除
        result = json.loads(content)
        
        # categoriesがない場合の保険
        if "categories" not in result:
            result["categories"] = ["雑費", "消耗品費", "その他"]

        return result
    
    #response.choices[0].message.contentは、APIからの応答の中で、最初の選択肢（choices[0]）のメッセージ（message）の内容（content）を取得するためのコード。json.loads()は、その内容をJSON形式からPythonの辞書に変換するための関数。
# .choices[0] = APIからの応答の中で、最初の選択肢を指します。APIは複数の選択肢を返すことがあるため、choicesはリスト形式で提供されます。ここでは、その最初の選択肢を使用しています。
# .message = APIからの応答の中で、選択肢のメッセージを指します。APIは通常、ユーザーの入力に対する応答をメッセージ形式で提供します。
# .content = メッセージの内容を指します。APIからの応答は通常、テキスト形式で提供されるため、contentには解析されたレシートの情報が含まれています。