import json
import re
from typing import List, Dict, Any
from decimal import Decimal
from app.core.config import settings


def _build_prompt(text: str) -> str:
    """Builds the shared financial parser prompt for both AI providers."""
    return f"""Kamu adalah mesin pengekstraksi transaksi keuangan (Financial Transaction Parser) berskala internasional untuk platform SpentTalk. Tugasmu adalah menganalisis pesan teks bebas dari pengguna dan mengubahnya menjadi format data JSON terstruktur yang valid.

Pesan pengguna: "{text}"

Patuhi instruksi ketat berikut untuk memperbaiki hasil ekstraksi:
1. DETEKSI MULTI-ITEM secara Menyeluruh: Analisis seluruh kalimat tanpa terkecuali. Jika pengguna menyebutkan lebih dari satu transaksi atau barang (misalnya dipisahkan kata 'dan', 'lalu', atau koma), kamu WAJIB mengekstrak SEMUA item tersebut ke dalam array "items". Jangan berhenti di item pertama.
2. MEMBERSIHKAN NAMA BARANG: Jangan pernah menyertakan kata kerja tindakan seperti "beli", "habis", "makan", "minum", "membayar", atau "jual" ke dalam properti "item_name". Ambil nama murni objek/barangnya saja secara rapi dengan format Capitalize (Contoh: "nasi padang" menjadi "Nasi Padang", "es teh" menjadi "Es Teh").
3. KONVERSI MATA UANG & SLANG: Kamu harus mengenali bahasa gaul keuangan Indonesia. Konversikan kata seperti "ribu", "rb", "k", "juta", "jt" menjadi angka desimal murni berbasis string (Contoh: "10rb" atau "10ribu" -> "10000.00"; "3ribu" -> "3000.00").
4. KATEGORISASI AKURAT: Tentukan nama kategori yang paling relevan untuk setiap barang (Contoh: Nasi Padang -> Makanan, Es Teh -> Minuman, Bensin -> Transportasi).
5. DETERMINASI TIPE: Tentukan properti "type" secara tepat, apakah berupa "pengeluaran" atau "pemasukan".

Kamu WAJIB mengembalikan output HANYA dalam format JSON murni yang mengikuti struktur objek di bawah ini, tanpa teks pengantar atau penutup apa pun:

{{
  "items": [
    {{
      "item_name": "Nama Barang Murni",
      "amount": "10000.00",
      "category_name": "Nama Kategori",
      "type": "pengeluaran/pemasukan"
    }}
  ]
}}"""


def _build_insight_prompt(financial_summary: Dict[str, Any]) -> str:
    """Builds the shared financial insight prompt for both AI providers."""
    return f"""Berikan analisis singkat dan saran keuangan untuk mahasiswa berdasarkan ringkasan keuangan berikut:
{json.dumps(financial_summary, default=str)}

Tulis dalam Bahasa Indonesia secara ramah, santai, dan informatif (maksimal 3 kalimat). Berikan peringatan jika pengeluaran kategori mendekati atau melebihi budget."""


def _clean_json_response(text: str) -> str:
    """Strips markdown code fences from an AI response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _normalize_parsed_items(data) -> List[Dict[str, Any]]:
    """Extracts the items list from the parsed JSON data and normalizes amounts."""
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    elif not isinstance(data, list):
        data = [data]

    for item in data:
        if "amount" in item:
            item["amount"] = float(item["amount"])

    return data


class GeminiProvider:
    """Google Gemini AI provider."""
    def __init__(self, api_key: str):
        import google.generativeai as genai
        self.genai = genai
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def generate(self, prompt: str) -> str:
        model = self.genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text

    @property
    def name(self) -> str:
        return "Gemini"


class GroqProvider:
    """Groq AI provider (uses llama models via Groq cloud)."""
    def __init__(self, api_key: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model_name = "llama-3.3-70b-versatile"

    def generate(self, prompt: str) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Kamu adalah asisten pengekstraksi transaksi keuangan untuk platform SpentTalk. Selalu kembalikan JSON murni tanpa teks tambahan."},
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            temperature=0.1,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content

    @property
    def name(self) -> str:
        return "Groq"


class NLPParser:
    """
    NLPParser handles interaction with AI providers (Gemini or Groq) to parse
    natural language text into financial data structures.
    Falls back to local rule-based parsing if all API calls fail.
    """
    def __init__(self):
        self.provider = None
        self.ai_provider_name = settings.ai_provider  # "gemini" or "groq"

        if self.ai_provider_name == "groq" and settings.groq_api_key:
            try:
                self.provider = GroqProvider(settings.groq_api_key)
                print(f"[NLPParser] AI Provider aktif: Groq (llama-3.3-70b-versatile)")
            except Exception as e:
                print(f"[NLPParser] Gagal inisialisasi Groq: {e}")
        elif self.ai_provider_name == "gemini" and settings.gemini_api_key:
            try:
                self.provider = GeminiProvider(settings.gemini_api_key)
                print(f"[NLPParser] AI Provider aktif: Gemini (gemini-2.5-flash)")
            except Exception as e:
                print(f"[NLPParser] Gagal inisialisasi Gemini: {e}")

        if not self.provider:
            print(f"[NLPParser] Tidak ada AI provider aktif. Menggunakan local fallback parser.")

    def parse_transaction(self, text: str) -> List[Dict[str, Any]]:
        """
        Sends natural language text to the active AI provider to extract transaction items.
        Returns a list of dicts with keys: item_name, amount, category_name, type.
        """
        if self.provider:
            prompt = _build_prompt(text)
            try:
                response_text = self.provider.generate(prompt)
                cleaned = _clean_json_response(response_text)
                data = json.loads(cleaned)
                return _normalize_parsed_items(data)
            except Exception as e:
                print(f"[NLPParser] {self.provider.name} API error, falling back to regex: {e}")

        # ---- Local Fallback Parser ----
        return self._local_parse(text)

    def generate_financial_insight(self, financial_summary: Dict[str, Any]) -> str:
        """
        Generates automated financial advice and budget warnings using the active AI provider.
        """
        if self.provider:
            prompt = _build_insight_prompt(financial_summary)
            try:
                response_text = self.provider.generate(prompt)
                return response_text.strip()
            except Exception as e:
                print(f"[NLPParser] {self.provider.name} API error for insight: {e}")

        # Local Fallback Insight
        return self._local_insight(financial_summary)

    # ---- Local Fallback Methods ----

    def _local_parse(self, text: str) -> List[Dict[str, Any]]:
        """Multi-item offline regex parser fallback."""
        parts = re.split(r'\b(?:dan|lalu|serta|\+)\b|,', text)
        extracted_items = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            part_lower = part.lower()

            # Determine type
            tx_type = "pemasukan" if any(x in part_lower for x in ["gaji", "pemasukan", "dapat", "transfer", "kiriman", "jajan bulanan", "penghasilan"]) else "pengeluaran"

            # Find and parse numbers (slang e.g., 10ribu, 10rb, 10k, 10000)
            amount = 10000.0
            num_match = re.search(r'(\d+(?:\.\d+)?)\s*(ribu|rb|k|juta|jt)?', part_lower)
            if num_match:
                val = float(num_match.group(1))
                suffix = num_match.group(2)
                if suffix:
                    if suffix in ["ribu", "rb", "k"]:
                        amount = val * 1000
                    elif suffix in ["juta", "jt"]:
                        amount = val * 1000000
                else:
                    if val < 1000:
                        amount = val * 1000
                    else:
                        amount = val

            # Clean item name: remove numbers and action/stop words
            clean_part = part
            if num_match:
                clean_part = clean_part.replace(num_match.group(0), "")

            verbs_and_stops = [
                r'\baku\b', r'\bsaya\b', r'\bhabis\b', r'\btadi\b', r'\bbeli\b', r'\bbayar\b',
                r'\bmakan\b', r'\bminum\b', r'\bmembayar\b', r'\bjual\b', r'\bdapat\b', r'\buntuk\b'
            ]
            for pat in verbs_and_stops:
                clean_part = re.sub(pat, "", clean_part, flags=re.IGNORECASE)

            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
            item_name = clean_part.title()
            if not item_name:
                item_name = "Transaksi"

            cat = "Lainnya"
            clean_lower = clean_part.lower()
            if any(x in clean_lower for x in ["makan", "nasi", "bakso", "padang", "warteg", "sate", "mie", "ayam"]):
                cat = "Makan"
            elif any(x in clean_lower for x in ["gojek", "grab", "bensin", "transport", "angkot", "mobil", "motor", "bus", "kereta"]):
                cat = "Transport"
            elif any(x in clean_lower for x in ["jajan", "snack", "chitato", "es", "camilan", "teh", "kopi", "minum", "jus", "bobba"]):
                cat = "Jajan"

            extracted_items.append({
                "item_name": item_name[:150],
                "amount": amount,
                "category_name": cat,
                "type": tx_type
            })

        if not extracted_items:
            extracted_items.append({
                "item_name": "Transaksi",
                "amount": 10000.0,
                "category_name": "Lainnya",
                "type": "pengeluaran"
            })

        return extracted_items

    def _local_insight(self, financial_summary: Dict[str, Any]) -> str:
        """Local fallback insight generator."""
        overruns = []
        for p in financial_summary.get("budget_progress", []):
            if p.get("percentage", 0) >= 100:
                overruns.append(p["name"])

        if overruns:
            warn_str = ", ".join(overruns)
            return f"Halo! Keuanganmu bulan ini terpantau stabil, namun harap berhati-hati karena budget untuk kategori **{warn_str}** sudah melebihi batas. Cobalah untuk lebih hemat di kategori tersebut ya!"

        return "Halo! Saldo dan budget belanjamu terpantau aman bulan ini. Teruskan kebiasaan mencatat transaksi secara disiplin dan hindari pengeluaran impulsif ya!"
