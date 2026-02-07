import pandas as pd
import os
from datetime import datetime

class InvoiceManager:
    def __init__(self, csv_path='invoices.csv'):
        self.csv_path = csv_path
        if not os.path.exists(csv_path):
            df = pd.DataFrame(columns=['Invoice_No', 'Date', 'Customer_Name', 'Total_Amount', 'Items_Count'])
            df.to_csv(csv_path, index=False)

    def log_invoice(self, invoice_no, customer_name, total_amount, items_count):
        new_entry = {
            'Invoice_No': invoice_no,
            'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Customer_Name': customer_name,
            'Total_Amount': total_amount,
            'Items_Count': items_count
        }
        df = pd.DataFrame([new_entry])
        df.to_csv(self.csv_path, mode='a', header=False, index=False)

    def get_history(self):
        if os.path.exists(self.csv_path):
            return pd.read_csv(self.csv_path)
        return pd.DataFrame()
