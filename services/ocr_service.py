# services/ocr_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OCR_API_KEY")

URL = "https://api.ocr.space/parse/image"

class OCRService:
    def __init__(self):
        if not API_KEY:
            raise ValueError("OCR_API_KEYが設定されていません")
        
        self.api_key = API_KEY
        self.url = URL

    def extract_text(self, image_url):
        response = requests.post(
            self.url,
            data={
                "apikey": self.api_key,
                "url": image_url,
                "language": "jpn",
                "isTable": True,
                "OCREngine": 2,
                "detectOrientation": True
            }
        )

        result = response.json()

        if result.get("IsErroredOnProcessing"):
            return "OCRエラー"

        if "ParsedResults" in result:
            return result["ParsedResults"][0]["ParsedText"]
        else:
            print("OCRエラー:", result)
            return ""