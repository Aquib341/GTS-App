import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from src.inventory_manager import InventoryManager
from src.ui_components import render_metric_card, render_stock_table, render_filters, render_inventory_grid
from src.validators import validate_price, validate_stock, validate_design_no
import time
from datetime import datetime
from src.invoice_generator import InvoiceGenerator
from src.invoice_manager import InvoiceManager
import base64

# Page Configuration
st.set_page_config(
    page_title="GTS",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Check for dummy credentials
import os
if os.path.exists("service_account.json"):
    with open("service_account.json", "r") as f:
        if "dummy-private-key" in f.read():
            st.sidebar.error("🚨 **ACTION REQUIRED**\n\nYour `service_account.json` contains dummy data.\n\nPlease update it with your actual Google Cloud credentials to enable connection.", icon="⚠️")

# Initialize Manager
if 'inventory_manager' not in st.session_state:
    st.session_state.inventory_manager = InventoryManager()

from src.auth import AuthManager
auth = AuthManager()

if not auth.check_password():
    st.stop()

manager = st.session_state.inventory_manager

if 'invoice_manager' not in st.session_state:
    st.session_state.invoice_manager = InvoiceManager()
invoice_manager = st.session_state.invoice_manager

# Sidebar Navigation
# Sidebar Navigation
# st.sidebar.markdown('<div class="logo-container"><img src="assets/logo.png" class="logo-img"></div>', unsafe_allow_html=True)
st.sidebar.image("assets/logo.png", use_container_width=True)
st.sidebar.title("GTS")

if st.sidebar.button("Logout", icon="🔒"):
    auth.logout()

page = st.sidebar.radio("Navigate", ["Home", "Dashboard", "Inventory", "Invoice", "History", "Connection", "Settings"])

if page == "Home":
    # Hero Section
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="shop-title">Govind Tiles & Sanitary</h1>', unsafe_allow_html=True)
    st.markdown('<p class="shop-subtitle">Premium Tiles, Granite, Marble & Sanitary Ware Solutions</p>', unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🏆</div>
            <h3>Premium Quality</h3>
            <p>Authorized dealer of top brands like Kajaria, Nitco, and more.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📦</div>
            <h3>Wholesale & Retail</h3>
            <p>Best prices for bulk orders and individual home needs.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🚚</div>
            <h3>Wide Range</h3>
            <p>Tiles, Granite, Marble, Sanitaryware - All under one roof.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Shop Details & Image Split
    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    
    with c1:
         st.image("assets/shop.jpeg", caption="Visit our Showroom in Banda", use_container_width=True)
         
    with c2:
        st.subheader("📍 Visit Us")
        st.markdown("""
        **Address:**  
        Tindwari Road, Kalu Kuwan, Banda, Uttar Pradesh, 210001
        
        **Contact:**  
        📞 9450168663, 8318155874
        
        **GSTIN:**  
        09BQNPG8011R1Z6
        
        **Business Hours:**  
        Mon - Sat: 10:00 AM - 8:00 PM
        """)
        
        st.info("💡 **Admin Note:** Use the sidebar to manage inventory or generate invoices.")

    # Search Section
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.subheader("🔍 Quick Layout Search")
    search_query = st.text_input("Find designs, brands, or sizes...", placeholder="e.g. 12x18, Nitco, Marble...")
    
    if search_query:
        df = manager.get_inventory()
        if not df.empty:
            mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
            results = df[mask]
            
            if not results.empty:
                st.success(f"Found {len(results)} items matching '{search_query}'")
                
                # Custom Grid for Results
                cols = st.columns(3)
                for idx, row in results.iterrows():
                    with cols[idx % 3]:
                        stock_val = pd.to_numeric(row.get('Current_Stock', 0), errors='coerce')
                        price_val = pd.to_numeric(row.get('Unit_Price', 0), errors='coerce')
                        
                        stock_class = "low" if stock_val < 10 else "normal"
                        
                        st.markdown(f"""
                        <div class="tile-card">
                            <div class="tile-img-placeholder">Tiles</div>
                            <div class="tile-content">
                                <div class="tile-header" title="{row['Tile_Name']}">{row['Tile_Name']}</div>
                                <div class="tile-sub">{row['Design_No']} | {row.get('Brand', 'Generic')}</div>
                                <div class="tile-meta">
                                    <span class="tile-price">₹{price_val:.2f}</span>
                                    <span class="tile-stock {stock_class}">{stock_val} in stock</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("") # Spacer
            else:
                st.warning("No items found.")
    st.markdown('</div>', unsafe_allow_html=True)


if page == "Dashboard":
    st.title("Dashboard")
    
    # Refresh logic
    if st.button("Refresh Data"):
        manager.refresh_data()
        st.rerun() # Use rerun instead of experimental_rerun
        
    # Stats
    stats = manager.get_stats()
    
    # Graceful degradation for stats if connection failed (stats all 0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Items", stats["total_items"])
    with col2:
        render_metric_card("Low Stock", stats["low_stock"]) 
    with col3:
        render_metric_card("Out of Stock", stats["out_of_stock"])
    with col4:
        render_metric_card("Total Value", f"₹{stats['total_value']:,.2f}")

    st.markdown("### 📊 Inventory Analytics & Insights")
    df = manager.get_inventory()
    
    if not df.empty:
        df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0)
        df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').fillna(0)
        df['Total_Value'] = df['Current_Stock'] * df['Unit_Price']
        
        # Clean data for Visualizations
        viz_df = df.copy()
        viz_df['Category'] = viz_df['Category'].fillna('Uncategorized').astype(str).replace('', 'Uncategorized')
        viz_df['Brand'] = viz_df['Brand'].fillna('Unknown').astype(str).replace('', 'Unknown')
        viz_df['Tile_Name'] = viz_df['Tile_Name'].fillna('Unknown Item').astype(str).replace('', 'Unknown Item')
        viz_df['Leaf_Label'] = viz_df['Tile_Name'] + " (" + viz_df['Design_No'].astype(str) + ")"

        # --- Row 1: High-Level Distribution ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("##### Stock Volume by Category (Treemap)")
            if 'Category' in df.columns and 'Brand' in df.columns:
                fig_tree = px.treemap(viz_df, path=[px.Constant("Inventory"), 'Category', 'Brand', 'Leaf_Label'], 
                                      values='Current_Stock',
                                      color='Current_Stock',
                                      color_continuous_scale='RdBu',
                                      color_continuous_midpoint=np.average(viz_df['Current_Stock'], weights=viz_df['Current_Stock']))
                fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350)
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("Category/Brand data missing for Treemap.")
                
        with c2:
            st.markdown("##### Value Distribution (Sunburst)")
            if 'Category' in df.columns:
                fig_sun = px.sunburst(viz_df, path=['Category', 'Brand'], values='Total_Value',
                                      color='Total_Value', color_continuous_scale='Greens')
                fig_sun.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=350)
                st.plotly_chart(fig_sun, use_container_width=True)
            else:
                st.info("Category data missing for Sunburst.")

        # --- Row 3: Operational Insights ---
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### Low Stock Alert Zones")
            # Scatter plot highlighting low stock items
            fig_scatter = px.scatter(df, x='Current_Stock', y='Unit_Price', 
                                     color='Status', size='Total_Value', hover_name='Tile_Name',
                                     title="Stock Level vs Price (Size = Value)")
            # Add a vertical line for min stock threshold (approx 10)
            fig_scatter.add_vline(x=10, line_width=1, line_dash="dash", line_color="red", annotation_text="Low Stock Threshold")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with c4:
            st.markdown("##### Price Density Distribution")
            fig_hist = px.histogram(df, x="Unit_Price", nbins=20, marginal="box", title="Unit Price Distribution")
            st.plotly_chart(fig_hist, use_container_width=True)

    else:
        st.info("No inventory data loaded to visualize.")

    st.markdown("### Quick Inventory View")
    # Quick view logic
    if not df.empty:
        # Show top 5 low stock items
        low_stock_df = df[pd.to_numeric(df['Current_Stock'], errors='coerce') < 10]
        low_stock_df = low_stock_df[low_stock_df['Current_Stock'] > 0] # Exclude out of stock
        
        if not low_stock_df.empty:
            st.warning(f"⚠️ {len(low_stock_df)} items are low on stock!")
            st.dataframe(low_stock_df.head(), use_container_width=True, hide_index=True)
        else:
            st.success("All stock levels represent healthy inventory.")
    else:
        st.info("No inventory data loaded. Please check connection or add items.")

elif page == "Inventory":
    st.title("Inventory Management")
    
    tab1, tab2 = st.tabs(["View & Edit", "Add New Item"])
    
    df = manager.get_inventory()
    
    with tab1:
        # Filters
        filtered_df = render_filters(df)
        
        # View Toggle
        col_t1, col_t2 = st.columns([6, 1])
        with col_t1:
            st.caption(f"Showing {len(filtered_df)} items")
        with col_t2:
            view_mode = st.radio("View", ["List", "Grid"], horizontal=True, label_visibility="collapsed")

        # Display content based on view mode
        if view_mode == "List":
            render_stock_table(filtered_df)
        else:
            render_inventory_grid(filtered_df)
        
        # --- Manage Inventory Section ---
        st.markdown("---")
        with st.expander("🛠️ Manage Inventory (Delete / Clear)", expanded=False):
            t1, t2 = st.tabs(["Delete Item", "Clear Dataset"])
            
            with t1:
                st.write("##### Delete Single Item")
                del_design_no = st.text_input("Enter Design No to Delete", placeholder="e.g. 1012 HL")
                if st.button("Delete Item", type="secondary", use_container_width=True):
                    if del_design_no:
                        with st.spinner("Deleting..."):
                            success, msg = st.session_state.inventory_manager.delete_item(del_design_no)
                            if success:
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("Please enter a Design No.")
            
            with t2:
                st.error("⚠️ **DANGER ZONE**")
                st.write("This will permanently delete ALL items from the inventory.")
                if st.button("DELETE ALL DATA", type="primary"):
                     st.session_state["confirm_delete_all"] = True
                
                if st.session_state.get("confirm_delete_all"):
                    st.warning("Are you absolutely sure?")
                    col_conf1, col_conf2 = st.columns(2)
                    with col_conf1:
                        if st.button("Yes, Delete Everything"):
                            with st.spinner("Wiping data..."):
                                success, msg = st.session_state.inventory_manager.clear_inventory()
                                if success:
                                    st.success(msg)
                                    st.session_state["confirm_delete_all"] = False
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with col_conf2:
                        if st.button("Cancel"):
                            st.session_state["confirm_delete_all"] = False
                            st.rerun()
        
        # Quick Update Section
        st.markdown("### Quick Stock Update")
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            # Dropdown for selecting item to update - better than text input
            if not filtered_df.empty:
                item_options = filtered_df['Design_No'].astype(str) + " - " + filtered_df['Tile_Name'].astype(str)
                selected_item_str = st.selectbox("Select Item", item_options)
                selected_design_no = selected_item_str.split(" - ")[0]
            else:
                st.info("No items to update.")
                selected_design_no = None

        with col2:
            qty_change = st.number_input("Change (+/-)", value=0, step=1)
            
        with col3:
            reasons = ["Sale", "Purchase", "Return", "Damage", "Adjustment"]
            reason = st.selectbox("Reason", reasons)
            
        with col4:
            if st.button("Update Stock"):
                if selected_design_no and qty_change != 0:
                    success, msg = manager.update_stock(
                        selected_design_no, 
                        qty_change, 
                        reason, 
                        user="Admin" # User auth not fully implemented yet
                    )
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                elif qty_change == 0:
                    st.warning("Quantity change cannot be 0")

    
    with tab2:
        st.subheader("Add New Item")
        
        # Choice between Single Item and Bulk Upload
        add_mode = st.radio("Add Mode", ["Single Item", "Bulk Upload (CSV/Excel)"], horizontal=True)
        
        if add_mode == "Single Item":
            with st.form("add_item_form"):
                col1, col2 = st.columns(2)
                with col1:
                    design_no = st.text_input("Design No")
                    tile_name = st.text_input("Tile Name")
                    category = st.selectbox("Category", ["Ceramic", "Porcelain", "Vitrified", "Mosaic", "Other"])
                    brand = st.text_input("Brand")
                    
                with col2:
                    size = st.text_input("Size (e.g. 60x60)")
                    unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01)
                    initial_stock = st.number_input("Initial Stock", min_value=0, step=1)
                    min_stock = st.number_input("Min Stock Alert", value=10, step=1)
                
                submitted = st.form_submit_button("Add Item")
                
                if submitted:
                    # Validation
                    is_valid_price, price_msg = validate_price(unit_price)
                    is_valid_stock, stock_msg = validate_stock(initial_stock)
                    
                    # Check duplicate design no
                    existing_nos = df['Design_No'].tolist() if not df.empty else []
                    is_valid_design, design_msg = validate_design_no(design_no, existing_nos)
                    
                    if not is_valid_price:
                        st.error(price_msg)
                    elif not is_valid_stock:
                        st.error(stock_msg)
                    elif not is_valid_design:
                        st.error(design_msg)
                    else:
                        item_data = {
                            "Design_No": design_no,
                            "Tile_Name": tile_name,
                            "Category": category,
                            "Brand": brand,
                            "Size": size,
                            "Current_Stock": initial_stock,
                            "Min_Stock": min_stock,
                            "Unit_Price": unit_price
                        }
                        success, msg = manager.add_new_item(item_data)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                            
        else: # Bulk Upload
            st.info("Upload a CSV or Excel file with columns: Design_No, Tile_Name, (optional: Category, Brand, Size, Current_Stock, Min_Stock, Max_Stock, Unit_Price)")
            
            uploaded_file = st.file_uploader("Choose file", type=['csv', 'xlsx'])
            
            if uploaded_file:
                if st.button("Import Data"):
                    with st.spinner("Importing..."):
                        success, msg = manager.bulk_import(uploaded_file)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                            
            with st.expander("Download Template"):
                with open("templates/inventory_template.csv", "rb") as f:
                    st.download_button("Download CSV Template", f, "inventory_template.csv", "text/csv")

elif page == "Invoice":
    st.title("📄 Invoice Generator")
    
    tab_new, tab_hist = st.tabs(["New Invoice", "Invoice History"])
    
    with tab_new:
        # Initialize Session State for Invoice Items
        if 'invoice_items' not in st.session_state:
            st.session_state.invoice_items = []
            
        col_inv1, col_inv2 = st.columns([1, 2])
        
        with col_inv1:
            st.subheader("Customer Details")
            with st.container(border=True):
                cust_name = st.text_input("Customer Name")
                cust_phone = st.text_input("Phone Number")
                cust_addr = st.text_area("Address", height=100)
        
        with col_inv2:
            st.subheader("Add Items")
            df = manager.get_inventory()
            
            if not df.empty:
                # Item Selection Config
                item_options = df['Design_No'].astype(str) + " - " + df['Tile_Name'].astype(str)
                selected_item_str = st.selectbox("Select Item", item_options, key="inv_item_select")
                
                if selected_item_str:
                    selected_design = selected_item_str.split(" - ")[0]
                    item_row = df[df['Design_No'].astype(str) == selected_design].iloc[0]
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        price_val = float(item_row.get('Unit_Price', 0))
                        inv_price = st.number_input("Unit Price", value=price_val, min_value=0.0)
                    with c2:
                        inv_qty = st.number_input("Quantity", min_value=1, value=1)
                    with c3:
                        st.write("Stock Available:")
                        st.write(f"**{item_row.get('Current_Stock', 0)}**")
                    
                    if st.button("Add to Invoice", type="primary"):
                        st.session_state.invoice_items.append({
                            "design_no": selected_design,
                            "name": item_row.get('Tile_Name', 'Unknown'),
                            "qty": inv_qty,
                            "price": inv_price,
                            "total": inv_qty * inv_price
                        })
                        st.success("Item Added!")
                        
        # Invoice Preview Table
        st.markdown("---")
        st.subheader("Invoice Preview")
        
        if st.session_state.invoice_items:
            inv_df = pd.DataFrame(st.session_state.invoice_items)
            
            st.dataframe(
                inv_df,
                column_config={
                    "name": "Item",
                    "qty": st.column_config.NumberColumn("Qty"),
                    "price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                    "total": st.column_config.NumberColumn("Total (₹)", format="₹%.2f")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Calculate Total
            grand_total = inv_df['total'].sum()
            st.markdown(f"### Total Amount: ₹{grand_total:,.2f}")
            
            c_act1, c_act2 = st.columns(2)
            with c_act1:
                if st.button("Clear Invoice"):
                    st.session_state.invoice_items = []
                    st.rerun()
                    
            with c_act2:
                if st.button("🖨️ Generate & Print Invoice", type="primary", use_container_width=True):
                    if not cust_name:
                        st.error("Please enter customer name.")
                    else:
                        shop_details = {
                            "name": "Govind Tiles & Sanitary",
                            "address": "Tindwari Road, Kalu Kuwan, Banda, Uttar Pradesh, 210001",
                            "gstin": "09BQNPG8011R1Z6",
                            "phone": "9450168663, 8318155874"
                        }
                        
                        customer_details = {
                            "name": cust_name,
                            "phone": cust_phone,
                            "address": cust_addr
                        }
                        
                        # Generate PDF
                        generator = InvoiceGenerator(shop_details)
                        pdf_buffer = generator.generate_invoice(
                            customer_details, 
                            st.session_state.invoice_items, 
                            grand_total
                        )
                        
                        pdf_val = pdf_buffer.getvalue()
                        b64_pdf = base64.b64encode(pdf_val).decode('utf-8')
                        
                        # Log to History
                        invoice_no = f"INV-{int(datetime.now().timestamp())}"
                        invoice_manager.log_invoice(
                            invoice_no, cust_name, grand_total, len(st.session_state.invoice_items)
                        )
                        
                        # Embed PDF
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                        
                        # Download Button Link
                        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="Invoice_{cust_name}_{datetime.now().strftime("%Y%m%d")}.pdf" class="stButton" style="text-decoration:none; padding:10px 20px; background-color:#1e293b; color:white; border-radius:5px;">Download PDF Invoice</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                        st.success("Invoice Generated & Logged! Print using the viewer above.")
                        
        else:
            st.info("Add items to start creating an invoice.")

    with tab_hist:
        st.subheader("Invoice History")
        hist_df = invoice_manager.get_history()
        if not hist_df.empty:
            st.dataframe(
                hist_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total_Amount": st.column_config.NumberColumn("Total (₹)", format="₹%.2f")
                }
            )
        else:
            st.info("No invoices generated yet.")

elif page == "History":
    st.title("📜 Transaction History")
    
    st.markdown("View changes made to the inventory in the last 7 days.")
    
    # Date Filter
    days = st.slider("Filter by days", min_value=1, max_value=30, value=7)
    
    history_df = manager.get_history(days=days)
    
    if not history_df.empty:
        # Styling the dataframe
        st.dataframe(
            history_df,
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Time", format="MMM DD, HH:mm"),
                "Design_No": "Design No",
                "Transaction_Type": "Type",
                "Quantity_Changed": st.column_config.NumberColumn("Change"),
                "New_Stock": "Stock After",
                "User": "User",
                "Reason": "Reason"
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Download Button
        csv = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download History CSV",
            csv,
            "inventory_history.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.info("No transactions found in this period. Make some updates to see them here!")

elif page == "Connection":
    st.title("Connection & Data")
    
    st.markdown("### 🔌 Connection Status")
    
    sheet_manager = manager.sheet_manager
    email = sheet_manager.get_client_email() # Define email here for use in connection status
    is_connected = sheet_manager.is_connected
    
    if is_connected:
        st.success(f"✅ Connected to: {email}")
        
        st.markdown("---")
        st.subheader("🔄 Synchronization")
        st.caption("If you see 'Item not found' errors, your Google Sheet might be empty. Use this to push all local data to the sheet.")
        
        if st.button("📤 Force Sync: Local -> Google Sheets"):
            with st.spinner("Syncing data... this may take a moment..."):
                success, msg = manager.sync_local_to_remote()
                if success:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)

    else:
        st.warning("⚠️ Not connected to Google Sheets.")
        st.info("To connect, upload your Service Account JSON below.")

    # Connection Details
    with st.container():
        st.markdown("#### Google Sheet Details")
        
        # Use columns for a better layout
        c1, c2 = st.columns(2)
        with c1:
            client_email = sheet_manager.get_client_email()
            st.text_input("Service Account Email", value=client_email, disabled=True, help="Share your Google Sheet with this email.")
        
        with c2:
            sheet_id = "17kKrgMVyuROFSuJJdRHSG7UBKHOLAyEO7wHsggmtEXk"
            st.text_input("Target Sheet ID", value=sheet_id, disabled=True)
            st.markdown(f"[➡️ Open Google Sheet](https://docs.google.com/spreadsheets/d/{sheet_id})")

        if st.button("🔄 Test / Reconnect"):
            with st.spinner("Testing connection..."):
                if sheet_manager.connect():
                    st.toast("Connection Successful!", icon="✅")
                    # Force init check
                    sheet_manager.initialize_sheet_if_empty()
                    st.rerun()
                else:
                    st.error("Connection Failed. Check logs/credentials.")

    st.markdown("---")
    
    # Credentials Update Section
    st.subheader("🔑 Update Credentials")
    with st.expander("Update Service Account JSON", expanded=not is_connected):
        st.info("Paste the content of your `service_account.json` file here to connect to Google Sheets.")
        
        # Load existing content if available for editing (but mask it partially for security if needed, or just show raw)
        current_content = ""
        if os.path.exists("service_account.json"):
            with open("service_account.json", "r") as f:
                current_content = f.read()
        
        json_input = st.text_area("Service Account JSON", value=current_content, height=300)
        
        if st.button("Save Credentials & Restart"):
            if not json_input.strip():
                st.error("Please paste the JSON content.")
            else:
                try:
                    # Validate JSON
                    import json
                    creds = json.loads(json_input)
                    if "private_key" not in creds or "client_email" not in creds:
                         st.error("Invalid JSON: Missing `private_key` or `client_email`.")
                    else:
                        with open("service_account.json", "w") as f:
                            f.write(json_input)
                        st.success("Credentials saved! Restarting app...")
                        time.sleep(1)
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("Invalid JSON format. Please check your input.")

    st.markdown("---")
    
    # Data Management
    st.markdown("### 💾 Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Export Data")
        st.caption("Download a backup of your current inventory.")
        df = manager.get_inventory()
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Inventory (CSV)",
                data=csv,
                file_name=f"stocksphere_inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data available to export.")
            
    with col2:
        st.subheader("Sync Status")
        if manager.last_fetch:
            st.info(f"Last Synced: {manager.last_fetch.strftime('%H:%M:%S')}")
        else:
            st.info("Last Synced: Never")
            
        if st.button("Force Sync Now"):
            manager.refresh_data()
            st.rerun()

elif page == "Settings":
    st.title("Settings")
    
    # User Preferences (Placeholder for now, but looks like "Real Settings")
    st.subheader("👤 User Profile")
    with st.container(border=True):
        st.write("**Current User:** Admin")
        st.write("**Role:** Administrator")
        if st.button("Log Out"):
            auth.logout()
            st.rerun()

    st.subheader("⚙️ Application Preferences")
    with st.container(border=True):
        t1, t2 = st.columns(2)
        with t1:
            st.toggle("Dark Mode Support", value=True, disabled=True, help="Theme is controlled by Streamlit config.")
            st.toggle("Notifications", value=True, help="Enable in-app notifications.")
        with t2:
            st.selectbox("Date Format", ["YYYY-MM-DD", "DD-MM-YYYY", "MM-DD-YYYY"])
            st.selectbox("Currency", ["₹ (INR)", "$ (USD)", "€ (EUR)"])
            
    st.subheader("🛠️ System Maintenance")
    with st.container(border=True):
        st.write("Cache Management")
        if st.button("Clear Application Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.toast("Cache cleared successfully!", icon="🧹")

    st.markdown("---")
    st.caption(f"StockSphere v1.0.0 | Built with Streamlit")
