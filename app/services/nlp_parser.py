import json
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from app.core.config import settings


def _build_prompt(text: str, user_categories: Optional[List[str]] = None) -> str:
    """Builds the shared hybrid chat & financial parser prompt for both AI providers."""
    # Build category instruction
    if user_categories:
        cat_list = ", ".join(user_categories)
        category_instruction = f"""- KATEGORISASI AKURAT: Pengguna memiliki kategori berikut di akun mereka: [{cat_list}].
      Kamu WAJIB memilih SALAH SATU dari daftar kategori di atas yang paling relevan untuk setiap barang.
      Panduan pemetaan:
      * Makanan/minuman yang mengenyangkan (nasi, bakso, mie ayam, soto, dll) -> pilih kategori Makan.
      * Minuman/cemilan ringan (es teh, kopi, jus, snack, dll) -> pilih kategori Jajan.
      * Transportasi (bensin, gojek, grab, parkir, tol, bus, kereta) -> pilih kategori Transport.
      * Jika tidak ada kategori yang cocok sama sekali, gunakan "Lainnya"."""
    else:
        category_instruction = """- KATEGORISASI AKURAT: Tentukan nama kategori yang paling relevan untuk setiap barang (Contoh: Nasi Padang -> Makan, Es Teh -> Jajan, Bensin -> Transport). Jika tidak cocok, gunakan "Lainnya"."""

    return f"""Kamu adalah asisten keuangan pribadi cerdas bernama SpentTalk. Tugasmu adalah menganalisis pesan dari pengguna secara cerdas.

Pesan pengguna: "{text}"

Patuhi instruksi ketat berikut:
1. KLASIFIKASI PESAN: Tentukan apakah pengguna sedang MENCATAT TRANSAKSI baru (pengeluaran atau pemasukan uang secara spesifik dengan nominal angka) ATAU sekadar ingin MENGOBROL, menyapa, bertanya tips keuangan, atau berkonsultasi secara umum.
   - Set properti "is_transaction" ke true jika pengguna berniat mencatat transaksi.
   - Set properti "is_transaction" ke false jika pengguna hanya mengobrol, menyapa, atau bertanya tentang hal-hal umum.

2. JIKA BUKAN TRANSAKSI (is_transaction = false):
   - Jawablah pesan pengguna dengan ramah, cerdas, solutif, dan informatif layaknya asisten keuangan pribadi yang profesional (maksimal 3-4 kalimat dalam Bahasa Indonesia).
   - Simpan jawaban tersebut pada properti "reply".
   - Biarkan array "items" bernilai kosong [].

3. JIKA MERUPAKAN TRANSAKSI (is_transaction = true):
   - Deteksi Multi-Item: Jika pengguna menyebutkan lebih dari satu barang (misal: "bakso 10k dan es teh 3k"), kamu WAJIB mengekstrak semua barang tersebut ke dalam array "items".
   - Bersihkan Nama Barang: Jangan pernah menyertakan kata kerja tindakan (beli, habis, makan, minum, dll) ke dalam "item_name". Format dengan Title Case.
   - Konversi nominal gaul (ribu, rb, k, juta, jt) menjadi angka Rupiah desimal murni string (Contoh: "7k" -> "7000.00"; "10rb" -> "10000.00"; "3ribu" -> "3000.00"; "1jt" -> "1000000.00").
   {category_instruction}
   - Determinasi Tipe: Tentukan "type" ("pengeluaran" atau "pemasukan") secara tepat berdasarkan kata kunci/konteks kalimat.
   - Buat rangkuman konfirmasi singkat di properti "reply" menggunakan format persis seperti contoh di bawah.

Kamu WAJIB mengembalikan output HANYA dalam format JSON murni yang mengikuti struktur objek di bawah ini, tanpa teks pengantar atau penutup apa pun:

{{
  "is_transaction": true,
  "reply": "Saya mendeteksi transaksi berikut:\\n- **Bakso** (Makan): -Rp 10,000\\n- **Es Teh** (Jajan): -Rp 3,000\\n\\nApakah data di atas sudah benar? (Ya/Tidak)",
  "items": [


    {{
      "item_name": "Nama Barang Murni",
      "amount": "10000.00",
      "category_name": "Nama Kategori",
      "type": "pengeluaran"
    }}
  ]
}}

ATAU jika bukan transaksi:

{{
  "is_transaction": false,
  "reply": "Respon obrolan asisten keuangan Anda di sini...",
  "items": []
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


def _normalize_parser_response(data: Any) -> Dict[str, Any]:
    """Ensures parser output follows the hybrid {"is_transaction", "reply", "items"} structure."""
    if not isinstance(data, dict):
        return {
            "is_transaction": True,
            "reply": "Saya mendeteksi transaksi berikut.",
            "items": _normalize_parsed_items(data)
        }

    is_tx = data.get("is_transaction", True)
    reply = data.get("reply", "")
    items_raw = data.get("items", [])

    normalized_items = _normalize_parsed_items(items_raw)

    if is_tx and not reply:
        reply = "Saya mendeteksi transaksi berikut."

    return {
        "is_transaction": is_tx,
        "reply": reply,
        "items": normalized_items
    }


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
                {"role": "system", "content": "Kamu adalah asisten keuangan pribadi cerdas bernama SpentTalk. Selalu kembalikan JSON murni tanpa teks tambahan."},
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
    natural language text into financial data structures or chat answers.
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

    def parse_transaction(self, text: str, user_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sends natural language text to the active AI provider to extract transaction items or chat.
        Accepts optional user_categories list to guide AI categorization.
        Returns a dict: {"is_transaction": bool, "reply": str, "items": list}
        """
        if self.provider:
            prompt = _build_prompt(text, user_categories)
            try:
                response_text = self.provider.generate(prompt)
                cleaned = _clean_json_response(response_text)
                data = json.loads(cleaned)
                return _normalize_parser_response(data)
            except Exception as e:
                print(f"[NLPParser] {self.provider.name} API error, falling back to regex: {e}")

        # ---- Local Fallback Parser ----
        return self._local_parse(text, user_categories)

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

    def _local_parse(self, text: str, user_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Multi-item offline regex parser fallback with smart categorization and basic chat detection."""
        text_lower = text.strip().lower()

        # Simple offline chat query checking
        chat_keywords = ["halo", "hi", "apa kabar", "tanya", "tips", "bagaimana", "saran", "siapa", "bantuan"]
        is_chat_only = any(x in text_lower for x in chat_keywords) and not any(char.isdigit() for char in text_lower)

        if is_chat_only:
            return {
                "is_transaction": False,
                "reply": "Halo! Saya adalah asisten keuangan pribadi Anda. Untuk mencatat pengeluaran atau pemasukan, ketik pesan beserta jumlah nominalnya (contoh: 'makan siang 15rb').",
                "items": []
            }

        parts = re.split(r'\b(?:dan|lalu|serta|\+)\b|,', text)
        extracted_items = []

        # Income keyword detection
        income_keywords = [
            "gaji", "pemasukan", "dapat", "terima", "diterima", "dikasih",
            "kiriman", "transfer masuk", "penghasilan", "honorarium", "bonus",
            "thr", "uang jajan", "hasil jualan", "freelance", "cashback",
            "dibayar", "menerima"
        ]

        for part in parts:
            part = part.strip()
            if not part:
                continue

            part_lower = part.lower()

            # Determine type
            tx_type = "pengeluaran"
            if any(x in part_lower for x in income_keywords):
                tx_type = "pemasukan"

            # Find and parse numbers
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

            # Clean item name
            clean_part = part
            if num_match:
                clean_part = clean_part.replace(num_match.group(0), "")

            verbs_and_stops = [
                r'\baku\b', r'\bsaya\b', r'\bhabis\b', r'\btadi\b', r'\bbeli\b', r'\bbayar\b',
                r'\bmakan\b', r'\bminum\b', r'\bmembayar\b', r'\bjual\b', r'\bdapat\b', r'\buntuk\b',
                r'\bterima\b', r'\bdikasih\b', r'\bdari\b', r'\bke\b'
            ]
            for pat in verbs_and_stops:
                clean_part = re.sub(pat, "", clean_part, flags=re.IGNORECASE)

            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
            item_name = clean_part.title()
            if not item_name:
                item_name = "Transaksi"

            # Smart categorization
            cat = "Lainnya"
            clean_lower = clean_part.lower()

            category_rules = {
                "Makan": ["nasi", "bakso", "mie", "ayam", "sate", "soto", "padang", "warteg",
                          "rendang", "gudeg", "rawon", "pecel", "lauk", "sayur", "rice",
                          "burger", "pizza", "kebab", "roti", "indomie", "makan", "lalapan",
                          "geprek", "seblak", "cilok", "batagor", "siomay", "dimsum",
                          "makanan", "food", "lunch", "dinner", "breakfast", "sarapan"],
                "Jajan": ["es", "teh", "kopi", "jus", "susu", "boba", "bobba", "coklat",
                          "snack", "chitato", "camilan", "gorengan", "kue", "roti",
                          "minuman", "drink", "jajan", "ice cream", "dessert", "cemilan",
                          "waffle", "crepes", "martabak", "terang bulan", "donat"],
                "Transport": ["gojek", "grab", "bensin", "parkir", "tol", "angkot",
                              "bus", "kereta", "ojek", "taxi", "mobil", "motor",
                              "transportasi", "transport", "pertalite", "pertamax",
                              "solar", "ongkir", "kirim", "pengiriman"]
            }

            for cat_name, keywords in category_rules.items():
                if any(x in clean_lower for x in keywords):
                    cat = cat_name
                    break

            extracted_items.append({
                "item_name": item_name[:150],
                "amount": amount,
                "category_name": cat,
                "type": tx_type
            })

        # Build transaction reply summary
        reply_lines = ["Saya mendeteksi transaksi berikut:"]
        for item in extracted_items:
            sign = "+" if item["type"] == "pemasukan" else "-"
            reply_lines.append(f"- **{item['item_name']}** ({item['category_name']}): {sign}Rp {item['amount']:,.0f}")
        reply_lines.append("\nApakah data di atas sudah benar? (Ya/Tidak)")


        reply_str = "\n".join(reply_lines)

        return {
            "is_transaction": True,
            "reply": reply_str,
            "items": extracted_items
        }

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

    def generate_overspending_check(self, financial_summary: Dict[str, Any]) -> str:
        """
        Analyzes financial summary using AI to detect overspending/wastes.
        """
        if self.provider:
            prompt = f"""Kamu adalah konsultan keuangan pribadi SpentTalk. Analisis ringkasan keuangan mahasiswa berikut untuk mengecek pemborosan atau kebocoran anggaran:
{json.dumps(financial_summary, default=str)}

Berikan analisis singkat (maksimal 3-4 kalimat) dalam Bahasa Indonesia yang ramah, santai, dan informatif. Sebutkan kategori mana saja yang boros (persentase budget >= 80% atau melebihi limit) atau jika tidak ada pemborosan, berikan apresiasi hangat."""
            try:
                response_text = self.provider.generate(prompt)
                return response_text.strip()
            except Exception as e:
                print(f"[NLPParser] {self.provider.name} API error for overspending check: {e}")

        # Local Fallback for Overspending
        overruns = []
        warning_80 = []
        for p in financial_summary.get("budget_progress", []):
            pct = p.get("percentage", 0)
            if pct >= 100:
                overruns.append(p["name"])
            elif pct >= 80:
                warning_80.append(p["name"])

        if overruns or warning_80:
            msg = "Hasil analisis cek pemborosan bulan ini:\n"
            if overruns:
                msg += f"- ⚠️ Kategori **{', '.join(overruns)}** sudah melebihi budget limit bulanan Anda!\n"
            if warning_80:
                msg += f"- ⚠️ Kategori **{', '.join(warning_80)}** sudah mendekati batas budget bulanan Anda (di atas 80%).\n"
            msg += "Cobalah untuk menahan diri dari belanja impulsif di kategori-kategori tersebut ya!"
            return msg

        return "Hebat! 🎉 Hasil analisis menunjukkan belum ada pemborosan terdeteksi bulan ini. Seluruh pengeluaran kategori Anda masih aman di bawah batas budget. Pertahankan kedisiplinan finansial ini ya!"

    def generate_saving_tips(self, financial_summary: Dict[str, Any]) -> str:
        """
        Generates personalized saving tips using AI based on user's financial state.
        """
        if self.provider:
            prompt = f"""Kamu adalah konsultan keuangan pribadi SpentTalk. Berikan tips menabung yang dipersonalisasi untuk mahasiswa berdasarkan ringkasan keuangan berikut:
{json.dumps(financial_summary, default=str)}

Berikan saran praktis dan langkah menabung (maksimal 3-4 kalimat) dalam Bahasa Indonesia yang ramah, santai, dan informatif yang paling relevan dengan kondisi saldo, pengeluaran, dan pendapatan mereka saat ini."""
            try:
                response_text = self.provider.generate(prompt)
                return response_text.strip()
            except Exception as e:
                print(f"[NLPParser] {self.provider.name} API error for saving tips: {e}")

        # Local Fallback for Saving Tips
        balance = float(financial_summary.get("saldo_terkini", 0))
        income = float(financial_summary.get("total_pemasukan_bulan_ini", 0))
        
        tips = [
            "Halo! Berikut tips menabung khusus untukmu saat ini:\n",
            "1. **Terapkan Aturan 50/30/20**: Alokasikan 50% uang jajanmu untuk kebutuhan utama, 30% keinginan, dan langsung tabung 20% di awal bulan.",
            "2. **Catat Setiap Kopi & Jajanan**: Pengeluaran kecil yang sering diabaikan (seperti jajanan/kopi) adalah kebocoran keuangan terbesar mahasiswa.",
            "3. **Gunakan Rekening Terpisah**: Simpan tabunganmu di rekening tanpa kartu ATM/M-Banking aktif untuk mencegah godaan belanja impulsif."
        ]
        return "\n".join(tips)
