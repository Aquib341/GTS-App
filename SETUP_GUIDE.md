# How to Connect StockSphere to Your Google Sheet

Currently, the app is running in **Demo Mode** with mock data because it cannot find your Google credentials. Follow these steps to connect it to your real inventory.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **New Project** (e.g., named "StockSphere").

## Step 2: Enable Google Sheets API

1. In your new project, search for "Google Sheets API" in the search bar.
2. Click **Enable**.
3. Search for "Google Drive API" and **Enable** it as well (required for opening sheets).

## Step 3: Create Service Account Credentials

1. Go to **APIs & Services > Credentials**.
2. Click **+ Create Credentials** > **Service Account**.
3. Name it `stocksphere-admin` and click **Create & Continue**.
4. Skip the optional role steps and click **Done**.
5. Click on the newly created service account (email looks like `...iam.gserviceaccount.com`).
6. Go to the **Keys** tab -> **Add Key** -> **Create new key** -> **JSON**.
7. A file will download automatically. **Rename this file to `service_account.json`**.

## Step 4: Add Credentials to Project

1. Move the `service_account.json` file into your **StockSphere project folder**:
   `/Users/aquib/Downloads/StockSphere/service_account.json`

## Step 5: Share Your Google Sheet

1. Create a new Google Sheet (or use your existing one).
2. Open the `service_account.json` file and copy the `client_email` address (e.g., `stocksphere-admin@...iam.gserviceaccount.com`).
3. Go to your Google Sheet, click **Share**, and paste this email address.
4. Give it **Editor** access.
5. Rename the Sheet tab (at the bottom) to **MASTER_INVENTORY** if it isn't already.

## Step 6: Restart the App

Stop the app (Ctrl+C) and run it again:

```bash
streamlit run app.py
```

The app will now detect the credentials and load your real data!
