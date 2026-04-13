# StockSphere: Smart Inventory & Billing Dashboard 📦

**StockSphere** is a production-ready, mobile-first inventory management and point-of-sale (POS) dashboard built with Python and Streamlit. It is designed to modernize retail shop operations (like "Govind Tiles & Sanitary") by providing real-time stock tracking, data analytics, invoice generation, and seamless synchronization with Google Sheets as a database backend.

## 🌟 Key Features

### 1. **Robust Inventory Management**
- **CRUD Operations**: Add single items or perform bulk uploads via CSV/Excel.
- **Low Stock Alerts**: Automated threshold tracking to notify when stock runs below minimum levels.
- **Smart Search & Filters**: Instantly find products by design number, brand, size, or category using an optimized pandas data pipeline.

### 2. **Advanced Analytics & Visualizations**
- **Interactive Dashboards**: Powered by **Plotly**, featuring Treemaps (stock volume by category), Sunburst charts (value distribution), and Scatter plots (price vs. stock levels).
- **Financial Metrics**: Real-time calculation of total inventory value and out-of-stock items.

### 3. **Automated Billing & Invoice Generation**
- **Dynamic Cart System**: Add items to a session-state managed cart.
- **PDF Generation**: Automatically generate professional PDF invoices using **ReportLab** with embedded shop details, customer info, and total calculations.
- **Invoice Logging**: Centralized tracking of all generated invoices for auditing.

### 4. **Resilient Data Architecture**
- **Google Sheets Integration**: Uses `gspread` and `google-oauth` to sync data seamlessly to cloud spreadsheets, allowing cross-device accessibility for shop owners.
- **Offline Fallback / Local Caching**: Maintains a local `inventory_local.csv` and transaction logs. The app remains fully functional even during internet outages, syncing changes back to the cloud when connectivity is restored.

### 5. **Security & Authentication**
- **Admin Gateway**: Basic authentication layer and role management to prevent unauthorized data manipulation.

---

## 🛠️ Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Data Engineering & Manipulation**: [Pandas](https://pandas.pydata.org/), NumPy
- **Data Visualization**: [Plotly Express](https://plotly.com/python/)
- **PDF & Document Engine**: [ReportLab](https://www.reportlab.com/)
- **Cloud Database / BaaS**: Google Sheets API, `gspread`, `google-auth`

---

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/StockSphere.git
cd StockSphere
```

### 2. Create a Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Google Sheets Database Configuration
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account**, generate a JSON key, and save it in the root folder as `service_account.json`.
4. Share your target Google Sheet with the client email found inside your `service_account.json` file.
5. Create a sheet tab named `MASTER_INVENTORY` and `TRANSACTION_LOG`.

### 4. Run the Application
```bash
streamlit run app.py
```

---

## 📂 Project Structure

```text
StockSphere/
├── app.py                     # Main application entry point & routing layer
├── requirements.txt           # Python dependencies
├── service_account.json       # Google Cloud credentials (not in version control)
├── SETUP_GUIDE.md             # Detailed connection instructions
├── .streamlit/                # Streamlit configuration overrides
│
├── src/                       # Application Core Logic
│   ├── inventory_manager.py   # State, Data fallback, and CRUD logic
│   ├── google_sheets.py       # Cloud DB connection and sync operations
│   ├── invoice_generator.py   # ReportLab PDF creation logic
│   ├── ui_components.py       # Modular Streamlit UI components
│   ├── auth.py                # Admin authentication gateway
│   └── validators.py          # Data validation schema 
│
├── assets/                    # CSS stylesheets and static images
└── templates/                 # CSV templates for bulk upload
```

---

## 🤝 Contribution

Contributions, issues, and feature requests are welcome! 
Feel free to check [issues page](https://github.com/yourusername/StockSphere/issues).

## 📝 License

This project is [MIT](LICENSE) licensed.
