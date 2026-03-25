import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Interactive Burndown Chart")

# Upload CSV
uploaded_file = st.file_uploader("Upload your tasks CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=['Created on','Completed on','Deadline'])
    
    # Data Cleaning (اختياري حسب المشروع)
    df['Completed on'] = pd.to_datetime(df['Completed on'])
    df['Created on'] = pd.to_datetime(df['Created on'])
    
    # Sidebar: Date range picker
    st.sidebar.header("Filter by Date")
    min_date = df['Created on'].min().date()
    max_date = df['Completed on'].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Convert selected dates to Timestamps
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Generate all days in selected range
    all_days = pd.date_range(start=start_date, end=end_date, freq='D')

    # Calculate remaining tasks per day
    remaining_tasks = []
    for day in all_days:
        remaining = df[df['Completed on'] > day].shape[0]
        remaining_tasks.append(remaining)

    # Create DataFrame for Burndown
    burndown_df = pd.DataFrame({
        'Date': all_days,
        'Remaining Tasks': remaining_tasks
    })

    # Plot Burndown Chart
    st.subheader(f"Burndown Chart ({start_date.date()} - {end_date.date()})")
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(burndown_df['Date'], burndown_df['Remaining Tasks'], marker='o', color='red', label='Remaining Tasks')
    
    # Optional: add ideal line
    ideal_line = [remaining_tasks[0] - i*(remaining_tasks[0]/(len(all_days)-1)) for i in range(len(all_days))]
    ax.plot(burndown_df['Date'], ideal_line, linestyle='--', color='green', label='Ideal Remaining')
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Remaining Tasks")
    ax.set_title("Burndown Chart")
    ax.grid(True)
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)