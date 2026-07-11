import sys
import os
from decimal import Decimal

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.services.nlp_parser import NLPParser
from app.core.database import db_manager
from app.models.base import Base

def test_gemini():
    print("=== Testing Google Gemini API connection ===")
    try:
        parser = NLPParser()
        key_display = f"{parser.api_key[:6]}...{parser.api_key[-6:]}" if parser.api_key else "None"
        print(f"Using API Key: {key_display}")
        
        # Test 1: NLP Parser
        test_text = "tadi beli nasi padang 15rb sama es teh 3rb"
        print(f"Sending sentence to parser: '{test_text}'")
        parsed_result = parser.parse_transaction(test_text)
        print("Success! Gemini Parsed JSON Output:")
        print(parsed_result)
        
        # Test 2: AI Insights
        test_summary = {
            "saldo_terkini": 500000.0,
            "total_pemasukan_bulan_ini": 1000000.0,
            "total_pengeluaran_bulan_ini": 800000.0,
            "budget_progress": [
                {"name": "makan", "spent": 400000.0, "limit": 300000.0, "percentage": 133.33},
                {"name": "jajan", "spent": 150000.0, "limit": 200000.0, "percentage": 75.00}
            ]
        }
        print("Requesting Gemini financial insight summary...")
        insight = parser.generate_financial_insight(test_summary)
        print("Success! Gemini Insight Output:")
        print(insight)
        return True
    except Exception as e:
        print(f"Error testing Gemini: {e}")
        return False

def test_database():
    print("\n=== Testing Database connection and table generation ===")
    try:
        connection = db_manager.engine.connect()
        print("Successfully connected to Aiven MySQL Server!")
        
        # Verify table registration
        print("Verifying/Initializing database tables...")
        Base.metadata.create_all(bind=db_manager.engine)
        print("Database tables validated/created successfully!")
        
        connection.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    gemini_ok = test_gemini()
    db_ok = test_database()
    
    print("\n=== TEST RESULTS SUMMARY ===")
    print(f"Gemini API: {'SUCCESS' if gemini_ok else 'FAILED'}")
    print(f"Aiven MySQL: {'SUCCESS' if db_ok else 'FAILED'}")
