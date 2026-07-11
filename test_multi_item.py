import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

# Register
client.post("/api/auth/register", json={"name":"Multi Test","email":"multi@test.com","password":"pass123","password_confirm":"pass123"})

# Login
r = client.post("/api/auth/login", json={"email":"multi@test.com","password":"pass123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Onboarding
client.put("/api/profile/onboarding", json={"initial_balance":1000000,"monthly_income":500000,"budgets":[]}, headers=headers)

# Test MULTI-ITEM chatbot
print("=== TES MULTI-ITEM CHATBOT ===")
r = client.post("/api/chatbot", json={"message":"aku habis beli nasi padang 10ribu dan es teh 3ribu"}, headers=headers)
data = r.json()
print(f"Status: {r.status_code}")
print(f"Reply:\n{data['reply']}")
print(f"\nJumlah item terdeteksi: {len(data['parse_result']['items'])}")
for i, item in enumerate(data["parse_result"]["items"]):
    print(f"  Item {i+1}: {item['item_name']} | Rp {float(item['amount']):,.0f} | Kategori: {item['category_name']} | Tipe: {item['type']}")

# Confirm all items
chat_id = data["parse_result"]["chat_message_id"]
r = client.post("/api/chatbot/confirm", json={"chat_message_id": chat_id, "confirmed": True}, headers=headers)
print(f"\nKonfirmasi: {r.json()['message']}")

# Check dashboard
r = client.get("/api/transactions/dashboard", headers=headers)
dash = r.json()
print(f"\n=== DASHBOARD ===")
print(f"Saldo Terkini: Rp {float(dash['saldo_terkini']):,.0f}")
print(f"Pengeluaran Bulan Ini: Rp {float(dash['total_pengeluaran_bulan_ini']):,.0f}")

# Check notifications
r = client.get("/api/notifications", headers=headers)
notifs = r.json()
print(f"\n=== NOTIFIKASI ({len(notifs)} total) ===")
for n in notifs:
    print(f"  [{n['type'].upper()}] {n['title']}: {n['message']}")

# Cleanup
client.delete("/api/auth/me", headers=headers)
print("\n=== TES MULTI-ITEM SELESAI ===")
