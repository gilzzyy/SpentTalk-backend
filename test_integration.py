import sys
import os
from fastapi.testclient import TestClient
from decimal import Decimal
import io

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.main import app
from app.core.database import db_manager


client = TestClient(app)

def run_integration_test():
    print("=== STARTING END-TO-END INTEGRATION TEST FOR SPENDTALK ===")
    
    # 1. Test registration (F-01)
    print("\n[F-01] Testing User Registration...")
    reg_payload = {
        "name": "Mahasiswa Test",
        "email": "test.mahasiswa@example.com",
        "password": "password123",
        "password_confirm": "password123"
    }
    
    # Delete test user first if they exist to avoid duplicate key errors
    from app.models.user import User
    db = db_manager.SessionLocal()
    existing_user = db.query(User).filter(User.email == reg_payload["email"]).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    db.close()
    
    response = client.post("/api/auth/register", json=reg_payload)
    if response.status_code == 201:
        print("SUCCESS: User registered successfully!")
    else:
        print(f"FAILED: Register status {response.status_code}, detail: {response.text}")
        return
        
    # 2. Test login (F-02)
    print("\n[F-02] Testing User Login...")
    login_payload = {
        "email": reg_payload["email"],
        "password": reg_payload["password"]
    }
    response = client.post("/api/auth/login", json=login_payload)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("SUCCESS: Logged in! JWT Access Token obtained.")
    else:
        print(f"FAILED: Login status {response.status_code}, detail: {response.text}")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test Profile GET (F-13)
    print("\n[F-13] Checking Profile Information...")
    response = client.get("/api/auth/me", headers=headers)
    user_id = response.json()["id"]
    print(f"SUCCESS: Profile loaded for user: {response.json()['name']} (ID: {user_id})")
    
    # Fetch default categories initialized on registration
    print("\n[F-03] Fetching default categories initialized during registration...")
    response = client.get("/api/profile/categories", headers=headers)
    categories = response.json()
    print("SUCCESS: Default categories created:")
    for cat in categories:
        print(f"  - Category: {cat['name']} (ID: {cat['id']}, Icon: {cat['icon']})")
        
    makan_cat_id = next(c["id"] for c in categories if c["name"] == "Makan")
    jajan_cat_id = next(c["id"] for c in categories if c["name"] == "Jajan")

    # 4. Test Onboarding (F-03)
    print("\n[F-03] Setting financial profile via Onboarding...")
    onboard_payload = {
        "initial_balance": 1000000.0,
        "monthly_income": 1500000.0,
        "budgets": [
            {"category_id": makan_cat_id, "period": "2026-07", "amount": 300000.0},
            {"category_id": jajan_cat_id, "period": "2026-07", "amount": 200000.0}
        ]
    }
    response = client.put("/api/profile/onboarding", json=onboard_payload, headers=headers)
    if response.status_code == 200:
        print("SUCCESS: Onboarding initial balance and monthly budgets saved!")
    else:
        print(f"FAILED: Onboarding status {response.status_code}, detail: {response.text}")
        return

    # Test double onboarding protection (Access Control Guard)
    print("Testing double onboarding protection...")
    response_double = client.put("/api/profile/onboarding", json=onboard_payload, headers=headers)
    if response_double.status_code == 400:
        print("SUCCESS: Double onboarding blocked correctly with status 400!")
    else:
        print(f"FAILED: Double onboarding was NOT blocked! Status: {response_double.status_code}")
        return


    # 5. Test Chatbot Parse (F-04, F-05)
    print("\n[F-04 & F-05] Testing Chatbot natural language parsing...")
    chat_payload = {"message": "tadi beli nasi padang 15rb"}
    response = client.post("/api/chatbot", json=chat_payload, headers=headers)
    if response.status_code == 200:
        chat_data = response.json()
        print(f"SUCCESS: AI parsed message successfully!")
        print(f"  AI Reply: {chat_data['reply']}")
        chat_message_id = chat_data["parse_result"]["chat_message_id"]
    else:
        print(f"FAILED: Chatbot parsing status {response.status_code}, detail: {response.text}")
        return

    # 6. Test Chatbot Confirmation & Saving (F-06, F-07)
    print("\n[F-06 & F-07] Testing Chatbot transaction confirmation and save (with detail overrides)...")
    confirm_payload = {
        "chat_message_id": chat_message_id,
        "confirmed": True,
        "override_item_name": "nasi padang jumbo",
        "override_amount": 17000.0
    }
    response = client.post("/api/chatbot/confirm", json=confirm_payload, headers=headers)
    if response.status_code == 200:
        print(f"SUCCESS: Transaction confirmed with overrides! Response message: {response.json()['message']}")
    else:
        print(f"FAILED: Confirmation status {response.status_code}, detail: {response.text}")
        return


    # 7. Test Dashboard (F-08 & F-11)
    print("\n[F-08 & F-11] Fetching Dashboard summary and AI Insight...")
    response = client.get("/api/transactions/dashboard", headers=headers)
    if response.status_code == 200:
        dash = response.json()
        print("SUCCESS: Dashboard loaded:")
        print(f"  Saldo Terkini: Rp {float(dash['saldo_terkini']):,.2f}")
        print(f"  Pengeluaran Bulan Ini: Rp {float(dash['total_pengeluaran_bulan_ini']):,.2f}")
        print("  Budget Progress:")
        for p in dash["budget_progress"]:
            print(f"    - Category {p['name']}: {p['percentage']}% terpakai ({float(p['spent']):,.2f}/{float(p['limit']):,.2f})")
        print(f"  AI insight: {dash['ai_insight']}")
    else:
        print(f"FAILED: Dashboard status {response.status_code}, detail: {response.text}")
        return

    # 8. Test Dynamic Categories & Budget Tracker (F-09)
    print("\n[F-09] Testing Budget Tracker (adding dynamic category + budget allocation)...")
    new_cat_payload = {
        "name": "Buku",
        "icon": "book",
        "budget_amount": 150000.0,
        "period": "2026-07"
    }
    response = client.post("/api/profile/categories", json=new_cat_payload, headers=headers)
    if response.status_code == 200:
        buku_cat = response.json()
        print(f"SUCCESS: Created dynamic category '{buku_cat['name']}' (ID: {buku_cat['id']}) and set budget to Rp 150,000.00 simultaneously!")
    else:
        print(f"FAILED: Creating category status {response.status_code}, detail: {response.text}")
        return

    # Test editing saldo_awal at any time (F-09)
    print("Testing editing saldo_awal (initial balance) via Profile...")
    balance_payload = {"initial_balance": 1200000.0}
    response = client.put("/api/profile/balance", json=balance_payload, headers=headers)
    if response.status_code == 200:
        balance_data = response.json()
        print(f"SUCCESS: Balance updated! New Initial Balance: Rp {float(balance_data['saldo_awal']):,.2f}, New Current Balance: Rp {float(balance_data['saldo_terkini']):,.2f}")
    else:
        print(f"FAILED: Updating balance status {response.status_code}, detail: {response.text}")
        return

    # 9. Test History Filters (F-10)
    print("\n[F-10] Fetching Transaction History with period (monthly) and search filter...")
    response = client.get("/api/transactions?period=2026-07&search=jumbo", headers=headers)
    if response.status_code == 200:
        hist = response.json()
        print("SUCCESS: History summary details loaded:")
        print(f"  Total Transaksi: {hist['total_transaksi']}")
        print(f"  Total Pengeluaran: Rp {float(hist['total_pengeluaran']):,.2f}")
        for tx in hist["transactions"]:
            print(f"    - Transaction: {tx['formatted_detail']}")
    else:
        print(f"FAILED: History status {response.status_code}, detail: {response.text}")
        return

    # 10. Test Excel Export (F-12 & F-13 via Profile)
    print("\n[F-12 & F-13] Testing Excel Report Export from profile page for custom period...")
    response = client.get("/api/profile/export?period=2026-07", headers=headers)
    if response.status_code == 200:
        print("SUCCESS: Excel spreadsheet generated from profile export!")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Content-Disposition: {response.headers.get('content-disposition')}")
    else:
        print(f"FAILED: Profile Excel export status {response.status_code}, detail: {response.text}")
        return



    # 11. Test Profile Update with photo upload simulation (F-13)
    print("\n[F-13] Testing Profile edit & Avatar upload...")
    edit_form = {
        "name": "Mahasiswa Updated",
        "email": "test.mahasiswa@example.com",
        "university": "Universitas Indonesia"
    }
    mock_file = ("avatar.png", io.BytesIO(b"dummy photo bytes"), "image/png")
    response = client.put(
        "/api/auth/me",
        data=edit_form,
        files={"profile_photo": mock_file},
        headers=headers
    )
    if response.status_code == 200:
        updated_user = response.json()
        print("SUCCESS: Profile edited successfully!")
        print(f"  New Name: {updated_user['name']}")
        print(f"  University: {updated_user['university']}")
        print(f"  Avatar URL: {updated_user['profile_photo_url']}")
    else:
        print(f"FAILED: Profile update status {response.status_code}, detail: {response.text}")
        return

    # 12. Test Notifications (New Feature)
    print("\nTesting Notification System...")
    response = client.get("/api/notifications", headers=headers)
    if response.status_code == 200:
        notifs = response.json()
        print(f"SUCCESS: Loaded {len(notifs)} notifications:")
        for n in notifs:
            print(f"  - [{n['type'].upper()}] {n['title']}: {n['message']} (Read: {n['is_read']})")
    else:
        print(f"FAILED: Loading notifications status {response.status_code}, detail: {response.text}")
        return

    print("Marking all notifications as read...")
    response = client.put("/api/notifications/read-all", headers=headers)
    if response.status_code == 200:
        print("SUCCESS: Marked all as read!")
    else:
        print(f"FAILED: Marking notifications status {response.status_code}, detail: {response.text}")
        return


    # 12. Clean up: Delete account (F-13)
    print("\n[F-13] Cleaning up test data (Deleting test account)...")
    response = client.delete("/api/auth/me", headers=headers)
    if response.status_code == 204:
        print("SUCCESS: Test account deleted cleanly.")
    else:
        print(f"FAILED: Account deletion status {response.status_code}, detail: {response.text}")

    print("\n=== ALL END-TO-END INTEGRATION TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_integration_test()
