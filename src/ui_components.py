import streamlit as st
import pandas as pd

def render_metric_card(title, value, delta=None, color="primary"):
    """
    Renders a metric card with optional delta and color.
    Uses HTML/CSS for custom styling as Streamlit's native metric is limited.
    """
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-delta">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_stock_table(df):
    """
    Renders the inventory table with custom styling for headers and rows.
    """
    if df.empty:
        st.info("No inventory data found. Add items to get started.")
        return

    # Apply some basic formatting for display
    display_df = df.copy()
    
    # Ensure numeric for display
    display_df['Current_Stock'] = pd.to_numeric(display_df['Current_Stock'], errors='coerce').fillna(0)
    display_df['Unit_Price'] = pd.to_numeric(display_df['Unit_Price'], errors='coerce').fillna(0)
    
    # Rename columns for friendly display if needed, but keeping them as is for now for clarity
    
    st.dataframe(
        display_df,
        column_config={
            "Unit_Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f", # Adjust currency symbol as needed
            ),
            "Current_Stock": st.column_config.NumberColumn(
                "Stock",
                format="%d",
            ),
            "Status": st.column_config.Column(
                "Status",
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True
    )

def render_filters(df):
    """
    Renders sidebar filters and returns filtered dataframe.
    """
    st.sidebar.header("Filters")
    
    if df.empty:
        return df

    # Search
    search_term = st.sidebar.text_input("Search (Design No, Name, Brand)", "")
    
    # Category Filter
    categories = ["All"] + sorted(list(set(df['Category'].dropna().astype(str))))
    selected_category = st.sidebar.selectbox("Category", categories)
    
    # Brand Filter
    brands = ["All"] + sorted(list(set(df['Brand'].dropna().astype(str))))
    selected_brand = st.sidebar.selectbox("Brand", brands)
    
    # Filter Logic
    filtered_df = df.copy()
    
    if search_term:
        # Case insensitive search across multiple columns
        mask = (
            filtered_df['Design_No'].astype(str).str.contains(search_term, case=False) |
            filtered_df['Tile_Name'].astype(str).str.contains(search_term, case=False) |
            filtered_df['Brand'].astype(str).str.contains(search_term, case=False)
        )
        filtered_df = filtered_df[mask]
        
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
        
    if selected_brand != "All":
        filtered_df = filtered_df[filtered_df['Brand'] == selected_brand]
        
    return filtered_df

def render_inventory_grid(df):
    """
    Renders inventory items as a grid of tile cards.
    """
    if df.empty:
        st.info("No items to display.")
        return

    # Ensure numeric types
    df['Current_Stock'] = pd.to_numeric(df['Current_Stock'], errors='coerce').fillna(0)
    df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').fillna(0)

    # CSS Grid Layout using Streamlit columns
    cols = st.columns(3) # 3 items per row
    
    for idx, row in df.iterrows():
        with cols[idx % 3]:
            # Determine stock class
            stock_class = "low" if row['Current_Stock'] < 5 else "normal"
            stock_label = "Low Stock" if row['Current_Stock'] < 5 else "In Stock"
            if row['Current_Stock'] == 0:
                stock_class = "low" # Red
                stock_label = "Out of Stock"
                
            # Card HTML
            html = f"""
            <div class="tile-card">
                <div class="tile-img-placeholder">
                    <span>{row['Design_No']}</span>
                </div>
                <div class="tile-content">
                    <div class="tile-header" title="{row['Tile_Name']}">{row['Tile_Name']}</div>
                    <div class="tile-sub">{row['Brand']} • {row['Size']}</div>
                    
                    <div class="tile-meta">
                        <span class="tile-price">₹{row['Unit_Price']:,.2f}</span>
                        <span class="tile-stock {stock_class}">{stock_label} ({int(row['Current_Stock'])})</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.write("") # Spacer
