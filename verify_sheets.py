import streamlit as st
from src.google_sheets import GoogleSheetManager
import sys

# Mock streamlit secrets if needed, but the manager handles local files too
# We rely on service_account.json being present (which it should be based on previous context)

def verify():
    print("--- Verifying Google Sheets Connection ---")
    manager = GoogleSheetManager()
    
    email = manager.get_client_email()
    print(f"Service Account Email: {email}")
    
    if not manager.is_connected:
        print("❌ Could not connect to Google API.")
        return
    
    print("✅ Connected to Google API.")
    
    sheet_id = "17kKrgMVyuROFSuJJdRHSG7UBKHOLAyEO7wHsggmtEXk"
    print(f"Attempting to open spreadsheet: {sheet_id}")
    
    sh = manager.get_spreadsheet(sheet_id)
    if sh:
        print(f"✅ Successfully opened spreadsheet: {sh.title}")
        
        # Try to read MASTER_INVENTORY
        try:
            ws = sh.worksheet("MASTER_INVENTORY")
            data = ws.get_all_records()
            print(f"✅ Read MASTER_INVENTORY. {len(data)} rows found.")
        except Exception as e:
            print(f"⚠️ Could not read MASTER_INVENTORY: {e}")
            print("Action: Initializing missing worksheets...")
            
            # Use the manager's initialize method
            success = manager.initialize_sheet_if_empty()
            if success:
                print("✅ Successfully initialized MASTER_INVENTORY and TRANSACTION_LOG with headers.")
            else:
                print("❌ Failed to initialize worksheets.")
            
        # Try to write to TRANSACTION_LOG
        try:
            log_ws = sh.worksheet("TRANSACTION_LOG")
            log_ws.append_row(["TEST_CONNECTION", "Verify Script", "Test", 0, 0, "System", "Connection Check"])
            print("✅ Successfully wrote test row to TRANSACTION_LOG.")
        except Exception as e:
             print(f"❌ Failed to write to TRANSACTION_LOG: {e}")
             
    else:
        print("❌ Failed to open spreadsheet.")
        print("   Possibilities:")
        print("   1. The email below is NOT an Editor on the sheet.")
        print("   2. The Sheet ID is incorrect.")
        print("   3. Google Sheets API is not enabled.")
        
        print("\n🔎 DIAGNOSTIC: Attempting to CREATE a test sheet to check API status...")
        try:
            new_sh = manager.client.create("StockSphere_Connection_Test")
            print("✅ SUCCESS: Created 'StockSphere_Connection_Test'.")
            print("conclusion: Google Sheets API is ENABLED. The issue is PERMISSIONS on the target sheet.")
            print(f"Action: Share your sheet with: {email}")
            # Clean up
            manager.client.del_spreadsheet(new_sh.id)
            print("   (Deleted test sheet)")
        except Exception as e:
            print(f"❌ FAILURE: Could not create a sheet. Error: {e}")
            print("conclusion: Google Sheets API might be DISABLED on your project.")
            print("Action: Go to console.cloud.google.com, search for 'Google Sheets API', and Enable it.")

if __name__ == "__main__":
    verify()
