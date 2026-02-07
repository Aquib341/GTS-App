import pandas as pd
import streamlit as st
from datetime import datetime
import os
import numpy as np
from src.google_sheets import GoogleSheetManager

LOCAL_CSV_PATH = "inventory_local.csv"

class InventoryManager:
    def __init__(self):
        self.sheet_manager = GoogleSheetManager()
        self.data = pd.DataFrame()
        self.last_fetch = None
        # Load local data immediately on init
        self.load_local_data()

    def load_local_data(self):
        """Loads data from local CSV if it exists."""
        if os.path.exists(LOCAL_CSV_PATH):
            try:
                self.data = pd.read_csv(LOCAL_CSV_PATH)
                # Ensure types
                if 'Current_Stock' in self.data.columns:
                    self.data['Current_Stock'] = pd.to_numeric(self.data['Current_Stock'], errors='coerce').fillna(0)
                if 'Unit_Price' in self.data.columns:
                    self.data['Unit_Price'] = pd.to_numeric(self.data['Unit_Price'], errors='coerce').fillna(0)
            except Exception as e:
                print(f"Failed to load local data: {e}")

    def save_local_data(self):
        """Saves current data to local CSV."""
        if not self.data.empty:
            self.data.to_csv(LOCAL_CSV_PATH, index=False)

    def refresh_data(self):
        """Forces a refresh of the data from Google Sheets, falling back to local."""
        st.cache_data.clear()
        
        # Try remote fetch
        if self.sheet_manager.is_connected:
            remote_data = self.sheet_manager.read_data("MASTER_INVENTORY")
            if not remote_data.empty:
                self.data = remote_data
                self.save_local_data() # Sync remote to local
                self.last_fetch = datetime.now()
                return self.data
        
        # Fallback to local if remote failed or disconnected
        if self.data.empty:
             self.load_local_data()
             
        # Fallback to template/mock if local is also empty
        if self.data.empty:
             self.data = self.get_mock_data()
             self.save_local_data()

        return self.data

    def get_mock_data(self):
        """Returns sample data for demonstration from the local template if available."""
        try:
            # Try loading the template file first
            template_path = "templates/inventory_template.csv"
            # Reading with flexible engine and handling potential parser errors
            df = pd.read_csv(template_path)
            
            # Map headers if needed or ensure standardization
            if "Design NO" in df.columns:
                df.rename(columns={"Design NO": "Design_No", "Quantity": "Current_Stock"}, inplace=True)
            
            # Basic cleaning similar to bulk_import
            if "Tile_Name" not in df.columns and "Design_No" in df.columns:
                 df["Tile_Name"] = df["Design_No"]
                 
            # Ensure proper types
            if 'Current_Stock' in df.columns:
                 df['Current_Stock'] = df['Current_Stock'].astype(str).str.replace(r'[a-zA-Z]', '', regex=True).str.strip()
                 df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0)
            
            # Add missing columns
            defaults = {
                "Category": "Uncategorized", 
                "Brand": "Generic", 
                "Size": "N/A", 
                "Min_Stock": 10, 
                "Max_Stock": 100, 
                "Unit_Price": 0, 
                "Status": "Active"
            }
            for col, val in defaults.items():
                if col not in df.columns:
                    df[col] = val
                    
            return df
        except Exception as e:
            # Fallback to hardcoded if file fails
            print(f"Failed to load template mock data: {e}")
            mock_data = {
                "Design_No": ["1012 HL", "5004"],
                "Tile_Name": ["Marble White", "Granite Black"],
                "Category": ["Ceramic", "Porcelain"],
                "Brand": ["Nitco", "Kajaria"],
                "Size": ["12x18", "60x60"],
                "Current_Stock": [45, 12],
                "Min_Stock": [10, 10],
                "Max_Stock": [100, 200],
                "Unit_Price": [45.50, 60.00],
                "Last_Updated": [datetime.now().strftime("%Y-%m-%d")] * 2,
                "Status": ["Active", "Active"]
            }
            return pd.DataFrame(mock_data)

    def get_inventory(self):
        """Returns the current inventory data, refreshing if necessary."""
        # Check if we should fetch remote? For now, trust local state unless forced refresh
        if self.data.empty:
            self.refresh_data()
        return self.data

    def get_stats(self):
        """Calculates quick stats for the dashboard."""
        df = self.get_inventory()
        if df.empty:
            return {
                "total_items": 0,
                "low_stock": 0,
                "out_of_stock": 0,
                "total_value": 0
            }
        
        # Ensure numeric columns are actually numeric
        df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0)
        df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').fillna(0)
        
        total_items = len(df)
        out_of_stock = len(df[df['Current_Stock'] <= 0])
        low_stock = len(df[(df['Current_Stock'] > 0) & (df['Current_Stock'] < 10)])
        
        total_value = (df['Current_Stock'] * df['Unit_Price']).sum()
        
        return {
            "total_items": total_items,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "total_value": total_value
        }

    def update_stock(self, design_no, quantity_change, reason, user="Admin"):
        """Updates stock locally and attempts remote sync."""
        df = self.get_inventory()
        if df.empty:
            return False, "Inventory is empty or failed to load."

        # Find the item
        df['Design_No'] = df['Design_No'].astype(str)
        item_row = df[df['Design_No'] == str(design_no)]
        
        if item_row.empty:
            return False, f"Item with Design No {design_no} not found."
            
        # Modify Local Data
        idx = item_row.index[0]
        current_stock = float(df.at[idx, 'Current_Stock'])
        new_stock = current_stock + float(quantity_change)
        
        if new_stock < 0:
            return False, f"Insufficient stock. Current: {current_stock}, Requested reduction: {abs(quantity_change)}"
            
        df.at[idx, 'Current_Stock'] = new_stock
        df.at[idx, 'Last_Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.data = df # Update class state
        self.save_local_data() # Persist to CSV
        
        # Log Transaction
        self.log_transaction(design_no, "Update" if quantity_change != 0 else "Edit", quantity_change, new_stock, user, reason)
        
        # Try Remote Update
        connection_msg = ""
        if self.sheet_manager.is_connected:
            try:
                success = self.sheet_manager.update_stock(design_no, new_stock)
                if success:
                     connection_msg = " (Synced to Google Sheets)"
                else:
                     connection_msg = " (Failed to sync remote)"
            except Exception as e:
                connection_msg = f" (Sync error: {str(e)})"
        else:
             connection_msg = " (Offline Mode - Local Only)"

        return True, f"Stock updated successfully.{connection_msg} New Stock: {new_stock}"

    def add_new_item(self, item_data):
        """Adds a new item to the inventory (Local + Remote)."""
        # item_data headers: Design_No, Tile_Name, Category, Brand, Size, Current_Stock, Min_Stock, Max_Stock, Unit_Price, Last_Updated, Status
        
        row_dict = {
            "Design_No": item_data.get("Design_No"),
            "Tile_Name": item_data.get("Tile_Name"),
            "Category": item_data.get("Category"),
            "Brand": item_data.get("Brand"),
            "Size": item_data.get("Size"),
            "Current_Stock": item_data.get("Current_Stock", 0),
            "Min_Stock": item_data.get("Min_Stock", 10),
            "Max_Stock": item_data.get("Max_Stock", 100),
            "Unit_Price": item_data.get("Unit_Price", 0),
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Active"
        }
        
        # Update Local
        self.data = pd.concat([self.data, pd.DataFrame([row_dict])], ignore_index=True)
        self.save_local_data()
        
        # Log Transaction
        self.log_transaction(item_data.get("Design_No"), "Add New Item", item_data.get("Current_Stock", 0), item_data.get("Current_Stock", 0), "Admin", "New Item Added")

        # Update Remote
        connection_msg = ""
        if self.sheet_manager.is_connected:
            row_list = list(row_dict.values())
            success = self.sheet_manager.append_row("MASTER_INVENTORY", row_list)
            if success:
                connection_msg = " (Synced to Google Sheets)"
            else:
                 connection_msg = " (Failed to sync remote)"
        else:
            connection_msg = " (Offline Mode - Local Only)"
            
        return True, f"Item added successfully.{connection_msg}"

    def bulk_import(self, file):
        """Imports data from a CSV or Excel file."""
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Normalization Logic (Same as before)
            if "Design NO" in df.columns:
                df.rename(columns={"Design NO": "Design_No", "Quantity": "Current_Stock"}, inplace=True)
            if "Tile_Name" not in df.columns and "Design_No" in df.columns:
                df["Tile_Name"] = df["Design_No"]
            if 'Current_Stock' in df.columns:
                df['Current_Stock'] = df['Current_Stock'].astype(str).str.replace(r'[a-zA-Z]', '', regex=True).str.strip()
                df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0)

            # Validate headers
            required_cols = ["Design_No"]
            if not all(col in df.columns for col in required_cols):
                return False, f"Missing required columns. Found: {list(df.columns)}. Expected at least: {required_cols}"
            
            # Default columns
            defaults = {
                "Tile_Name": "Unknown", "Category": "Uncategorized", "Brand": "Generic", 
                "Size": "N/A", "Current_Stock": 0, "Min_Stock": 10, 
                "Max_Stock": 100, "Unit_Price": 0, "Status": "Active"
            }
            for col, val in defaults.items():
                if col not in df.columns:
                    df[col] = val
            
            df['Last_Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Deduplication
            existing_data = self.get_inventory()
            if not existing_data.empty and 'Design_No' in existing_data.columns:
                existing_designs = set(existing_data['Design_No'].astype(str))
                df = df[~df['Design_No'].astype(str).isin(existing_designs)]
            
            if df.empty:
                return True, "No new items to import (duplicates skipped)."
            
            # Append local
            self.data = pd.concat([self.data, df], ignore_index=True)
            self.save_local_data()
            
            # Attempt Remote Append
            count = 0
            if self.sheet_manager.is_connected:
                # Prepare list for sheets
                for _, row in df.iterrows():
                     # Construct ordered list based on sheet expected headers
                     # Design_No, Tile_Name, Category, Brand, Size, Current_Stock, Min_Stock, Max_Stock, Unit_Price, Last_Updated, Status
                     row_list = [
                        row['Design_No'], row['Tile_Name'], row.get('Category'), row.get('Brand'),
                        row.get('Size'), row.get('Current_Stock'), row.get('Min_Stock'),
                        row.get('Max_Stock'), row.get('Unit_Price'), 
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Active"
                     ]
                     self.sheet_manager.append_row("MASTER_INVENTORY", row_list)
                     count += 1
                return True, f"Successfully imported {len(df)} items locally and {count} remotely."
            
            # Log Import
            self.log_transaction("Bulk Import", "Import", len(df), len(self.data), "Admin", f"Imported {len(df)} items")
            return True, f"Successfully imported {len(df)} items locally (Offline)."
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    def log_transaction(self, design_no, transaction_type, quantity_change, new_stock, user, reason):
        """Logs a transaction locally and remotely."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "Timestamp": timestamp,
            "Design_No": str(design_no),
            "Transaction_Type": transaction_type,
            "Quantity_Changed": quantity_change,
            "New_Stock": new_stock,
            "User": user,
            "Reason": reason
        }
        
        # 1. Local Log
        try:
            log_path = "transaction_log.csv"
            new_log = pd.DataFrame([log_entry])
            if os.path.exists(log_path):
                new_log.to_csv(log_path, mode='a', header=False, index=False)
            else:
                new_log.to_csv(log_path, mode='w', header=True, index=False)
        except Exception as e:
            print(f"Failed to log locally: {e}")

        # 2. Remote Log
        if self.sheet_manager.is_connected:
            try:
                # Prepare list for sheets: Timestamp, Design_No, Transaction_Type, Quantity_Change, New_Stock, User, Reason
                row_list = [
                    timestamp, str(design_no), transaction_type, 
                    quantity_change, new_stock, user, reason
                ]
                self.sheet_manager.append_row("TRANSACTION_LOG", row_list)
            except Exception:
                pass # Fail silently for remote log if connection drops

    def get_history(self, days=7):
        """Retrieves transaction history for the last N days."""
        log_path = "transaction_log.csv"
        try:
            if not os.path.exists(log_path):
                return pd.DataFrame()
            
            df = pd.read_csv(log_path)
            if df.empty:
                return pd.DataFrame()

            # Filter by date
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            filtered_df = df[df['Timestamp'] >= cutoff_date]
            
            # Sort by latest first
            return filtered_df.sort_values(by='Timestamp', ascending=False)
        except Exception as e:
            st.error(f"Error reading history: {e}")
            return pd.DataFrame()

    def delete_item(self, design_no):
        """Deletes an item from local and remote inventory."""
        try:
            design_no = str(design_no)
            
            # 1. Local Deletion
            if not self.data.empty:
                self.data['Design_No'] = self.data['Design_No'].astype(str)
                initial_len = len(self.data)
                self.data = self.data[self.data['Design_No'] != design_no]
                
                if len(self.data) < initial_len:
                    self.save_local_data()
                else:
                    return False, "Item not found locally."

            # 2. Remote Deletion
            connection_msg = ""
            if self.sheet_manager.is_connected:
                try:
                    ws = self.sheet_manager.get_spreadsheet().worksheet("MASTER_INVENTORY")
                    cell = ws.find(design_no)
                    if cell:
                        ws.delete_rows(cell.row)
                        st.cache_data.clear()
                        connection_msg = " (Synced to Google Sheets)"
                    else:
                        connection_msg = " (Item not found in Google Sheets)"
                except Exception as e:
                    connection_msg = f" (Remote delete failed: {str(e)})"
            else:
                 connection_msg = " (Offline Mode - Local Only)"
            
            self.log_transaction(design_no, "Delete", 0, 0, "Admin", "Item Deleted")
            return True, f"Item deleted successfully.{connection_msg}"
        except Exception as e:
            return False, f"Deletion error: {str(e)}"

    def clear_inventory(self):
        """Clears all inventory data."""
        try:
            # 1. Local Clear
            self.data = pd.DataFrame()
            if os.path.exists(LOCAL_CSV_PATH):
                os.remove(LOCAL_CSV_PATH)
            
            # 2. Remote Clear
            connection_msg = ""
            if self.sheet_manager.is_connected:
                try:
                    ws = self.sheet_manager.get_spreadsheet().worksheet("MASTER_INVENTORY")
                    ws.clear()
                    # Re-add headers
                    headers = [
                        "Design_No", "Tile_Name", "Category", "Brand", "Size", 
                        "Current_Stock", "Min_Stock", "Max_Stock", "Unit_Price", 
                        "Last_Updated", "Status"
                    ]
                    ws.append_row(headers)
                    st.cache_data.clear()
                    connection_msg = " (Synced to Google Sheets)"
                except Exception as e:
                    connection_msg = f" (Remote clear failed: {str(e)})"
            else:
                 connection_msg = " (Offline Mode - Local Only)"
            
            self.log_transaction("ALL", "Clear Inventory", 0, 0, "Admin", "Full Inventory Wipe")
            self.refresh_data()
            return True, f"Inventory cleared.{connection_msg}"
        except Exception as e:
            return False, f"Clear error: {str(e)}"

    def sync_local_to_remote(self):
        """Pushes all local data to the remote Google Sheet, overwriting it."""
        if not self.sheet_manager.is_connected:
            return False, "Not connected to Google Sheets."
            
        if self.data.empty:
            return False, "Local inventory is empty. Nothing to sync."
            
        try:
            # Ensure sheet exists
            try:
                ws = self.sheet_manager.get_spreadsheet().worksheet("MASTER_INVENTORY")
                ws.clear()
            except Exception:
                # If missing, create it
                ws = self.sheet_manager.get_spreadsheet().add_worksheet(title="MASTER_INVENTORY", rows=1000, cols=20)
            
            # Headers
            headers = [
                "Design_No", "Tile_Name", "Category", "Brand", "Size", 
                "Current_Stock", "Min_Stock", "Max_Stock", "Unit_Price", 
                "Last_Updated", "Status"
            ]
            ws.append_row(headers)
            
            # Prepare rows
            # Sanitization for JSON compliance (NaN/Inf -> 0 or "")
            sync_df = self.data.copy()
            sync_df = sync_df.fillna(0) # Simple fill for all NaNs
            # Replace infinite values if any
            import numpy as np
            sync_df = sync_df.replace([np.inf, -np.inf], 0)

            rows_to_add = []
            for _, row in sync_df.iterrows():
                row_list = [
                    row.get('Design_No'), row.get('Tile_Name'), row.get('Category'), row.get('Brand'),
                    row.get('Size'), row.get('Current_Stock'), row.get('Min_Stock'),
                    row.get('Max_Stock'), row.get('Unit_Price'), 
                    row.get('Last_Updated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                    row.get('Status', 'Active')
                ]
                rows_to_add.append(row_list)
            
            # Batch update/append is better, but append_rows (plural) isn't in standard gspread without version check
            # We'll stick to a loop or use update. 
            # Ideally, use ws.update([headers] + rows_to_add) but that requires precise range logic or gspread update method.
            # Safe bet: append_rows if available, or loop. gspread v6 has append_rows.
            
            # Checking if 'append_rows' exists in client, assuming standard gspread
            if hasattr(ws, 'append_rows'):
                ws.append_rows(rows_to_add)
            else:
                 # Fallback
                 for r in rows_to_add:
                     ws.append_row(r)
            
            st.cache_data.clear()
            return True, f"Successfully synced {len(self.data)} items to Google Sheets."
        except Exception as e:
            return False, f"Sync failed: {str(e)}"
