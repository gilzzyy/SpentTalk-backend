import json
from typing import List, Dict, Any
import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import APIConnectionError

class NLPParser:
    """
    NLPParser handles interaction with Google Gemini API to parse natural language text into financial data structures.
    """
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = "gemini-1.5-flash"

    def parse_transaction(self, text: str) -> List[Dict[str, Any]]:
        """
        Sends natural language text to Gemini API to extract transaction items.
        Returns a list of dicts with keys: item_name, amount, category, type.
        """
        if not self.api_key:
            # Fallback mock for offline/no-key development
            return [
                {
                    "item_name": f"Mock item from '{text[:20]}'",
                    "amount": 10000.0,
                    "category": "jajan",
                    "type": "expense"
                }
            ]

        prompt = f"""
        Ekstrak transaksi keuangan dari teks berikut: "{text}"
        
        Keluarkan data dalam format JSON murni berupa list of objects. Setiap object harus memiliki key berikut:
        - "item_name": nama barang atau deskripsi transaksi (string)
        - "amount": nominal transaksi (angka decimal/float)
        - "category": kategori transaksi, pilih salah satu dari: makan, transport, jajan, lainnya, pemasukan (string)
        - "type": tipe transaksi, pilih "income" (untuk pemasukan) atau "expense" (untuk pengeluaran) (string)
        
        JSON:
        """
        
        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            # Clean response text to ensure it only parses JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            if not isinstance(data, list):
                data = [data]
            return data
        except Exception as e:
            raise APIConnectionError("Google Gemini API", str(e))

    def generate_financial_insight(self, financial_summary: Dict[str, Any]) -> str:
        """
        Generates automated financial advice and budget warnings using Gemini API.
        """
        if not self.api_key:
            return "Kunci API Gemini belum dikonfigurasi. Silakan isi API key di file .env untuk mengaktifkan AI Insight."

        prompt = f"""
        Berikan analisis singkat dan saran keuangan untuk mahasiswa berdasarkan ringkasan keuangan berikut:
        {json.dumps(financial_summary, default=str)}
        
        Tulis dalam Bahasa Indonesia secara ramah dan informatif (maksimal 3 kalimat). Berikan peringatan jika budget kategori melebihi 60% atau over-budget.
        """
        
        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Gagal memuat insight keuangan: {str(e)}"
