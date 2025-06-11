import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Online Retail Sales Dashboard",
    page_icon="🛒",
    layout="wide"
)

# --- Caching Function for Data Loading ---
@st.cache_data
def load_data(file_path):
    """
    Loads, cleans, and preprocesses the online retail data.
    This function is cached to improve performance.
    """
    try:
        # Load the dataset
        df = pd.read_csv(file_path, encoding='ISO-8859-1')

        # --- Data Cleaning and Preprocessing ---
        # Convert InvoiceDate to datetime objects
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

        # Drop rows with missing CustomerID, as they are hard to analyze
        df.dropna(subset=['CustomerID'], inplace=True)

        # Convert CustomerID to integer type
        df['CustomerID'] = df['CustomerID'].astype(int)

        # Remove returns/cancelled orders (Quantity < 0)
        df = df[df['Quantity'] > 0]
        
        # Remove entries with zero or negative unit price, as they don't represent a sale
        df = df[df['UnitPrice'] > 0]

        # Create a 'TotalPrice' column
        df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
        
        # Extract time-based features for analysis
        df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
        df['Hour'] = df['InvoiceDate'].dt.hour
        df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()


        return df

    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure it's in the same directory as the script.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

# --- Main Application ---
def main():
    # --- Title and Introduction ---
    st.markdown("<h1 style='text-align: center;'>🛒 Online Retail Sales Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("""
    Welcome to the interactive sales dashboard for the Online Retail dataset.
    This application allows you to analyze sales trends, top products, customer behavior, and regional performance.
    Use the filters below to refine the data.
    """)

    # --- Load Data ---
    df = load_data('Online_Retail.csv')

    if df is not None:
        # --- Filters (moved from sidebar to main page) ---
        with st.expander("📊 Adjust Filters", expanded=True):
            all_countries = sorted(df['Country'].unique())
            
            # Checkbox to select/deselect all countries
            select_all = st.checkbox("Select All / Deselect All Countries")
            
            # Determine the default selection for the multiselect
            if select_all:
                default_selection = all_countries
            else:
                default_selection = ['United Kingdom']

            selected_countries = st.multiselect(
                "Select Country/Countries",
                options=all_countries,
                default=default_selection
            )

        if not selected_countries:
            st.warning("Please select at least one country from the filter menu to view the dashboard.")
            st.stop()
            
        # Filter dataframe based on selection
        filtered_df = df[df['Country'].isin(selected_countries)]

        # --- Display Key Metrics ---
        st.header("Key Performance Indicators (KPIs)")
        
        total_revenue = filtered_df['TotalPrice'].sum()
        total_orders = filtered_df['InvoiceNo'].nunique()
        unique_customers = filtered_df['CustomerID'].nunique()
        total_items_sold = filtered_df['Quantity'].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"£{total_revenue:,.2f}")
        col2.metric("Total Orders", f"{total_orders:,}")
        col3.metric("Unique Customers", f"{unique_customers:,}")
        col4.metric("Items Sold", f"{total_items_sold:,}")
        
        st.markdown("---")

        # --- Visualizations ---
        st.header("Data Visualizations")

        # 1. Monthly Sales Trend
        st.subheader("Monthly Sales Trend")
        monthly_sales = filtered_df.groupby('InvoiceMonth')['TotalPrice'].sum().reset_index()
        monthly_sales = monthly_sales.sort_values('InvoiceMonth')
        
        fig_monthly = px.line(
            monthly_sales, 
            x='InvoiceMonth', 
            y='TotalPrice', 
            title='Total Revenue Over Time',
            labels={'InvoiceMonth': 'Month', 'TotalPrice': 'Total Revenue (£)'},
            markers=True
        )
        fig_monthly.update_layout(xaxis={'type': 'category'}) # Treat month strings as categories
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        st.markdown("---")
        
        # 2. Top N Products
        st.subheader("Top 10 Best-Selling Products")
        top_products = filtered_df.groupby('Description')['Quantity'].sum().nlargest(10).reset_index()
        fig_products = px.bar(
            top_products, 
            x='Quantity', 
            y='Description', 
            orientation='h', 
            title='Top 10 Products by Quantity Sold'
        )
        fig_products.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_products, use_container_width=True)

        st.markdown("---")

        # Create two columns for the next charts
        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
            # 3. Sales by Hour of the Day
            st.subheader("Sales by Hour of the Day")
            hourly_sales = filtered_df.groupby('Hour')['TotalPrice'].sum().reset_index()
            fig_hourly = px.bar(
                hourly_sales,
                x='Hour',
                y='TotalPrice',
                title='Total Revenue by Hour of Day',
                labels={'Hour': 'Hour of Day (24-hour format)', 'TotalPrice': 'Total Revenue (£)'}
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

        with col_viz2:
            # 4. Sales by Day of the Week
            st.subheader("Sales by Day of the Week")
            daily_sales = filtered_df.groupby('DayOfWeek')['TotalPrice'].sum().reset_index()
            # Ensure days are sorted correctly
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            daily_sales['DayOfWeek'] = pd.Categorical(daily_sales['DayOfWeek'], categories=days_order, ordered=True)
            daily_sales = daily_sales.sort_values('DayOfWeek')
            
            fig_daily = px.bar(
                daily_sales,
                x='DayOfWeek',
                y='TotalPrice',
                title='Total Revenue by Day of the Week',
                labels={'DayOfWeek': 'Day of the Week', 'TotalPrice': 'Total Revenue (£)'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)


        # --- Display DataFrames ---
        st.markdown("---")
        st.header("Data Explorer")
        
        show_cleaned_data = st.checkbox("Show Cleaned & Filtered Data")
        if show_cleaned_data:
            st.dataframe(filtered_df.head(100))

        show_raw_data = st.checkbox("Show Original Raw Data")
        if show_raw_data:
            raw_df = pd.read_csv('Online_Retail.csv', encoding='ISO-8859-1')
            st.dataframe(raw_df.head(100))


if __name__ == "__main__":
    main()
