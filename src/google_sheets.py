import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import json
import os

class GoogleSheetManager:
    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = None
        self.spreadsheet = None

    def connect(self):
        """Connects to Google Sheets using Streamlit secrets or local file."""
        try:
            # Check secrets.toml safely
            creds = None
            try:
                if "gcp_service_account" in st.secrets:
                   creds_dict = st.secrets["gcp_service_account"]
                   creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            except FileNotFoundError:
                # No secrets.toml file found, ignore and try local file
                pass
            except Exception:
                pass

            # If not found in secrets, try local file
            if not creds and os.path.exists("service_account.json"):
                try:
                    # Check for dummy data first to avoid cryptic PEM errors
                    with open("service_account.json", "r") as f:
                        file_content = f.read()
                        if "dummy-private-key" in file_content or "dummy-project" in file_content:
                            # Use warning instead of error for better UX in demo mode
                            if "demo_mode_shown" not in st.session_state:
                                st.warning("ℹ️ Using Demo Data: `service_account.json` contains placeholder credentials. To enable Google Sheets sync, replace it with your valid key file.")
                                st.session_state["demo_mode_shown"] = True
                            return None
                    
                    creds = Credentials.from_service_account_file("service_account.json", scopes=self.scope)
                except ValueError as ve:
                    # This catches the "Could not deserialize key data" (PEM error)
                    st.error(f"⚠️ specific: Invalid `service_account.json` format. The private key might be malformed.")
                    return None
                except Exception as e:
                     st.error(f"⚠️ Error loading service_account.json: {str(e)}")
                     return None
            
            if not creds:
                # Only show this if we didn't already show a specific error above
                # But since we return None above, this is for the case where file doesn't exist at all
                if not os.path.exists("service_account.json"):
                    if "demo_mode_shown" not in st.session_state:
                         st.warning("ℹ️ No `service_account.json` found. App running in offline demo mode.")
                         st.session_state["demo_mode_shown"] = True
                return None

            client = gspread.authorize(creds)
            return client
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            return None

    def get_client_email(self):
        """Returns the client email from the service account credentials."""
        try:
            if self.client and self.client.auth:
                 return self.client.auth.service_account_email
            
            # Fallback
            try:
                if "gcp_service_account" in st.secrets:
                    return st.secrets["gcp_service_account"].get("client_email")
            except FileNotFoundError:
                pass
                
            if os.path.exists("service_account.json"):
                try:
                    with open("service_account.json") as f:
                        data = json.load(f)
                        return data.get("client_email", "Unknown")
                except json.JSONDecodeError:
                    return "Invalid JSON"
            return "Not Configured"
        except Exception:
            return "Unknown"

    @property
    def is_connected(self):
        """Checks if the client is successfully connected."""
        if self.client is None:
            self.client = self.connect()
        return self.client is not None

    def get_spreadsheet(self, sheet_key_or_url="1IIkVwxqhECDir4ujpWid1JyXdyj2lRbmZTjoHtdXMag"):
        """Opens the spreadsheet by key or URL. Defaults to the user's provided sheet."""
        if self.client is None:
            self.client = self.connect()
            if self.client is None:
                if "demo_mode_notified" not in st.session_state:
                    st.toast("Using Demo Data (No Connection)", icon="ℹ️")
                    st.session_state["demo_mode_notified"] = True
                return None
        
        try:
            # Try opening by key (ID) first as it's most robust
            return self.client.open_by_key(sheet_key_or_url)
        except gspread.SpreadsheetNotFound:
            try:
                # Fallback: try opening by name if the key fails (though unlikely for ID)
                 return self.client.open("StockSphere_DB")
            except gspread.SpreadsheetNotFound:
                 # If provided sheet not found, we can't easily "create" it at that specific ID. 
                 # We must notify user.
                 st.error(f"Spreadsheet with ID '{sheet_key_or_url}' not found. Please ensure you have shared it with {self.get_client_email()}")
                 return None
        except Exception as e:
            st.error(f"Error opening spreadsheet: {e}")
            return None

    def initialize_sheet_if_empty(self):
        """Checks if the connected sheet has required headers and initializes if empty."""
        if not self.is_connected:
            return False
            
        sh = self.get_spreadsheet()
        if not sh:
            return False
            
        try:
            # Check MASTER_INVENTORY
            try:
                ws = sh.worksheet("MASTER_INVENTORY")
            except gspread.WorksheetNotFound:
                ws = sh.add_worksheet(title="MASTER_INVENTORY", rows=1000, cols=20)
                
            if not ws.get_all_records():
                headers = [
                    "Design_No", "Tile_Name", "Category", "Brand", "Size", 
                    "Current_Stock", "Min_Stock", "Max_Stock", "Unit_Price", 
                    "Last_Updated", "Status"
                ]
                ws.append_row(headers)
                
            # Check TRANSACTION_LOG
            try:
                log_ws = sh.worksheet("TRANSACTION_LOG")
            except gspread.WorksheetNotFound:
                log_ws = sh.add_worksheet(title="TRANSACTION_LOG", rows=1000, cols=10)
                
            if not log_ws.get_all_records():
                 log_headers = [
                    "Timestamp", "Design_No", "Transaction_Type", 
                    "Quantity_Changed", "New_Stock", "User", "Reason"
                ]
                 log_ws.append_row(log_headers)
                 
            return True
        except Exception as e:
            st.error(f"Initialization error: {e}")
            return False

    @st.cache_data(ttl=30)
    def read_data(_self, worksheet_name):
        """Reads data from a specific worksheet into a DataFrame."""
        try:
            if _self.spreadsheet is None:
                _self.spreadsheet = _self.get_spreadsheet()
                if _self.spreadsheet is None:
                    return pd.DataFrame() # Return empty if still fails
            
            try:
                ws = _self.spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                # Auto-initialize if missing
                _self.initialize_sheet_if_empty()
                try:
                    ws = _self.spreadsheet.worksheet(worksheet_name)
                except:
                    return pd.DataFrame()

            data = ws.get_all_records()
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            st.error(f"Error reading data: {e}")
            return pd.DataFrame()

    def update_cell(self, worksheet_name, row_idx, col_idx, value):
        """Updates a specific cell."""
        try:
            if self.spreadsheet is None:
                self.spreadsheet = self.get_spreadsheet()
                if self.spreadsheet is None:
                    return False
            
            ws = self.spreadsheet.worksheet(worksheet_name)
            # gspread uses 1-based indexing
            ws.update_cell(row_idx, col_idx, value)
            st.cache_data.clear() # Clear cache to reflect updates
            return True
        except Exception as e:
            st.error(f"Error updating cell: {e}")
            return False

    def append_row(self, worksheet_name, row_data):
        """Appends a row to the worksheet."""
        try:
            if self.spreadsheet is None:
                self.spreadsheet = self.get_spreadsheet()
                if self.spreadsheet is None:
                    return False
            
            ws = self.spreadsheet.worksheet(worksheet_name)
            ws.append_row(row_data)
            st.cache_data.clear() # Clear cache
            return True
        except Exception as e:
            st.error(f"Error appending row: {e}")
            return False

    def update_stock(self, design_no, new_stock):
        """Optimized method to find and update stock for a specific design no."""
        try:
            if self.spreadsheet is None:
                self.spreadsheet = self.get_spreadsheet()
                if self.spreadsheet is None:
                    return False
            
            ws = self.spreadsheet.worksheet("MASTER_INVENTORY")
            cell = ws.find(str(design_no))
            if cell:
                # Assuming 'Current_Stock' is column 6 (F) based on headers
                # Design_No (1), Tile_Name (2), ..., Current_Stock (6)
                # But it's safer to map headers
                headers = ws.row_values(1)
                try:
                    col_idx = headers.index("Current_Stock") + 1
                except ValueError:
                     # Fallback if header not found
                     col_idx = 6

                ws.update_cell(cell.row, col_idx, new_stock)
                
                # Update Last_Updated as well
                try:
                    time_col_idx = headers.index("Last_Updated") + 1
                    ws.update_cell(cell.row, time_col_idx, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                except:
                    pass
                
                st.cache_data.clear()
                return True
            else:
                st.error("Item not found")
                return False
        except Exception as e:
            st.error(f"Error updating stock: {e}")
            return False
