import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt

# --- Page Configuration ---
st.set_page_config(
    page_title="Customer & Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Caching Functions for Data Loading ---
@st.cache_data
def load_sales_data(file_path):
    """
    Loads, cleans, and preprocesses the main sales data.
    """
    try:
        df = pd.read_csv(file_path, encoding='ISO-8859-1')
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
        df.dropna(subset=['Customer ID'], inplace=True)
        df['Customer ID'] = df['Customer ID'].astype(int)
        df = df[df['Quantity'] > 0]
        df = df[df['Price'] > 0]
        df['TotalPrice'] = df['Quantity'] * df['Price']
        df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
        df['Hour'] = df['InvoiceDate'].dt.hour
        df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()
        return df
    except Exception as e:
        st.error(f"Error loading sales data from '{file_path}': {e}")
        return None

@st.cache_data
def load_rfm_data(file_path):
    """
    Loads the RFM segmentation data.
    """
    try:
        rfm_df = pd.read_csv(file_path)
        rfm_df.rename(columns={
            'recency': 'Recency',
            'frequency': 'Frequency',
            'monetary': 'Monetary',
            'segment': 'Segment'
        }, inplace=True)
        return rfm_df
    except Exception as e:
        st.error(f"Error loading RFM data from '{file_path}': {e}")
        return None

# --- Main Application ---
def main():
    st.markdown("<h1 style='text-align: center;'>📈 Customer & Sales Analytics Dashboard</h1>", unsafe_allow_html=True)

    # --- UPDATED ORDER: General Sales Dashboard now comes first ---

    # --- Load Sales Data ---
    df = load_sales_data('combined_data.csv')

    # --- General Sales Dashboard Section ---
    if df is not None:
        st.header("General Sales Dashboard")

        with st.expander("📊 Adjust Sales Data Filters", expanded=True):
            all_countries = sorted(df['Country'].unique())
            select_all = st.checkbox("Select All / Deselect All Countries", value=True)

            if select_all:
                default_selection = all_countries
            else:
                default_selection = ['United Kingdom'] if 'United Kingdom' in all_countries else []

            selected_countries = st.multiselect(
                "Select Country/Countries for Sales Analysis",
                options=all_countries,
                default=default_selection
            )

        if not selected_countries:
            st.warning("Please select at least one country to view the sales dashboard.")
            st.stop()

        filtered_df = df[df['Country'].isin(selected_countries)]

        st.subheader("Key Performance Indicators (KPIs)")
        total_revenue = filtered_df['TotalPrice'].sum()
        total_orders = filtered_df['Invoice'].nunique()
        unique_customers = filtered_df['Customer ID'].nunique()
        total_items_sold = filtered_df['Quantity'].sum()

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Total Revenue", f"£{total_revenue:,.2f}")
        kpi_col2.metric("Total Orders", f"{total_orders:,}")
        kpi_col3.metric("Unique Customers", f"{unique_customers:,}")
        kpi_col4.metric("Items Sold", f"{total_items_sold:,}")

        st.markdown("---")

        st.subheader("Sales Trends and Breakdowns")
        monthly_sales = filtered_df.groupby('InvoiceMonth')['TotalPrice'].sum().reset_index().sort_values('InvoiceMonth')
        fig_monthly = px.line(monthly_sales, x='InvoiceMonth', y='TotalPrice', title='Total Revenue Over Time', markers=True)
        fig_monthly.update_layout(xaxis={'type': 'category'})
        st.plotly_chart(fig_monthly, use_container_width=True)

        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            top_products = filtered_df.groupby('Description')['Quantity'].sum().nlargest(10).reset_index()
            fig_products = px.bar(top_products, x='Quantity', y='Description', orientation='h', title='Top 10 Products by Quantity Sold')
            fig_products.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_products, use_container_width=True)

        with viz_col2:
            daily_sales = filtered_df.groupby('DayOfWeek')['TotalPrice'].sum().reset_index()
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            daily_sales['DayOfWeek'] = pd.Categorical(daily_sales['DayOfWeek'], categories=days_order, ordered=True)
            daily_sales = daily_sales.sort_values('DayOfWeek')
            fig_daily = px.bar(daily_sales, x='DayOfWeek', y='TotalPrice', title='Total Revenue by Day of the Week')
            st.plotly_chart(fig_daily, use_container_width=True)

        st.markdown("---")


    # --- UPDATED ORDER: RFM Customer Segmentation Analysis now comes second ---

    # --- Load RFM Data ---
    rfm_df = load_rfm_data('rfm.csv')

    # --- RFM Customer Segmentation Analysis Section ---
    if rfm_df is not None:
        st.header("RFM Customer Segmentation Analysis")
        st.markdown("""
        This section provides a deep dive into customer segments based on the **RFM (Recency, Frequency, Monetary)** model.
        Use these insights to develop targeted marketing campaigns and improve customer retention. This analysis is independent of the filters above.
        """)

        color_sequence = px.colors.qualitative.Plotly
        all_segments = rfm_df['Segment'].unique()
        color_map = {segment: color for segment, color in zip(all_segments, color_sequence)}

        st.subheader("Customer Segment Distribution")
        dist_col1, dist_col2 = st.columns(2)
        segment_counts = rfm_df['Segment'].value_counts()

        with dist_col1:
            fig_segment_bar = px.bar(
                segment_counts,
                x=segment_counts.index,
                y=segment_counts.values,
                color=segment_counts.index,
                color_discrete_map=color_map,
                title="Number of Customers in Each Segment",
                labels={'x': 'Segment', 'y': 'Number of Customers'}
            )
            fig_segment_bar.update_layout(xaxis={'categoryorder':'array', 'categoryarray': [
                'hibernating', 'loyal_customers', 'champions', 'at_risk',
                'potential_loyalists', 'about_to_sleep', 'need_attention',
                'promising', 'cant_loose', 'new_customers'
            ]})
            st.plotly_chart(fig_segment_bar, use_container_width=True)

        with dist_col2:
            fig_segment_pie = px.pie(
                segment_counts,
                names=segment_counts.index,
                values=segment_counts.values,
                color=segment_counts.index,
                color_discrete_map=color_map,
                title="Percentage of Customers in Each Segment",
                hole=0.3
            )
            st.plotly_chart(fig_segment_pie, use_container_width=True)

        st.markdown("---")

        st.subheader("Segment Value and Behavior Analysis")

        fig_treemap = px.treemap(
            rfm_df,
            path=[px.Constant("All Customers"), 'Segment'],
            values='Monetary',
            color='Segment',
            color_discrete_map=color_map,
            title='Total Monetary Value Contribution by Segment'
        )
        fig_treemap.update_traces(
            textinfo='label+value+percent root',
            textfont={'size': 16, 'color': 'white'}
        )
        fig_treemap.update_layout(margin=dict(t=50, l=25, r=25, b=25))
        st.plotly_chart(fig_treemap, use_container_width=True)

        mean_freq = rfm_df.groupby('Segment')['Frequency'].mean().reset_index()
        custom_order = [
            'hibernating', 'loyal_customers', 'champions', 'at_risk',
            'potential_loyalists', 'about_to_sleep', 'need_attention',
            'promising', 'cant_loose', 'new_customers'
        ]
        mean_freq['Segment'] = pd.Categorical(mean_freq['Segment'], categories=custom_order, ordered=True)
        mean_freq = mean_freq.sort_values('Segment')
        
        sorted_freq = mean_freq.sort_values(by='Frequency', ascending=False)
        max_freq = mean_freq['Frequency'].max()
        min_freq = mean_freq['Frequency'].min()
        
        highest_segments = mean_freq[mean_freq['Frequency'] == max_freq]['Segment'].tolist()
        lowest_segments = mean_freq[mean_freq['Frequency'] == min_freq]['Segment'].tolist()

        def assign_color_group(segment):
            if segment in highest_segments:
                return 'Highest Frequency'
            elif segment in lowest_segments:
                return 'Lowest Frequency'
            else:
                return 'Mid-Range'

        mean_freq['ColorGroup'] = mean_freq['Segment'].apply(assign_color_group)
        
        freq_color_map = {
            'Highest Frequency': 'mediumseagreen',
            'Lowest Frequency': 'crimson',
            'Mid-Range': 'royalblue'
        }

        fig_freq_bar = px.bar(
            mean_freq,
            x='Segment',
            y='Frequency',
            color='ColorGroup',
            color_discrete_map=freq_color_map,
            title='Average Purchase Frequency by Segment',
            labels={'Segment': 'Segment', 'Frequency': 'Average Number of Purchases'}
        )
        st.plotly_chart(fig_freq_bar, use_container_width=True)

if __name__ == "__main__":
    main()