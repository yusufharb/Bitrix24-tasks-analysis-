import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Load Data
# -------------------------
st.title("Project Tasks Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload your tasks CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=['Created on','Completed on','Deadline'])

    # -------------------------
    # Data Cleaning & Categorization
    # -------------------------
    testers = ['Yara Mahmoud', 'Muhammed Talaat']
    regular_user = 'Ahmed Abdelfattah'
    frontend_team = ['Anwar Abdelmaksoud', 'ammar elkhouly', 'Omar Adly']
    backend_team = ['Mohamed Salah', 'Mahmoud Abdelhamid', 'Ahmad Maghrapy']

    def categorize_task(row):
        if row['Created by'] in testers:
            return 'Bug'
        elif row['Created by'] == regular_user:
            return 'Regular Task'
        elif row['Assignee'] in frontend_team:
            return 'Frontend Task'
        elif row['Assignee'] in backend_team:
            return 'Backend Task'
        else:
            return 'Other'

    df['Task Category'] = df.apply(categorize_task, axis=1)
    df['Is Bug'] = df['Created by'].isin(testers)
    df['Completion Time (days)'] = (df['Completed on'] - df['Created on']).dt.days
    df['Is Late'] = df['Completed on'] > df['Deadline']
    df['Is Completed'] = df['Status'].str.lower().str.contains('complete', na=False)

    # -------------------------
    # Sidebar Filters
    # -------------------------
    st.sidebar.header("Filters")
    assignee_filter = st.sidebar.multiselect("Select Assignee", df['Assignee'].unique(), default=df['Assignee'].unique())
    category_filter = st.sidebar.multiselect("Select Task Category", df['Task Category'].unique(), default=df['Task Category'].unique())
    status_filter = st.sidebar.multiselect("Select Status", df['Status'].unique(), default=df['Status'].unique())

    df_filtered = df[
        (df['Assignee'].isin(assignee_filter)) &
        (df['Task Category'].isin(category_filter)) &
        (df['Status'].isin(status_filter))
    ]

    # -------------------------
    # Overview Section (CEO)
    # -------------------------
    st.header("📊 Overview")
    total_tasks = len(df_filtered)
    completed_tasks = df_filtered['Is Completed'].sum()
    completion_rate = completed_tasks / total_tasks * 100 if total_tasks > 0 else 0
    total_bugs = df_filtered['Is Bug'].sum()
    avg_completion_time = df_filtered['Completion Time (days)'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Completed Tasks", completed_tasks)
    col3.metric("Completion Rate %", f"{completion_rate:.1f}%")
    col4.metric("Total Bugs", total_bugs)

    # Tasks distribution
    st.subheader("Tasks Distribution by Category")
    fig1, ax1 = plt.subplots()
    df_filtered['Task Category'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax1)
    ax1.set_ylabel("")
    st.pyplot(fig1)

    # -------------------------
    # Detailed Section (PM)
    # -------------------------
    st.header("📋 Detailed Analysis")

    # Tasks per Assignee
    st.subheader("Tasks per Assignee")
    fig2, ax2 = plt.subplots(figsize=(10,4))
    df_filtered['Assignee'].value_counts().plot(kind='bar', ax=ax2)
    st.pyplot(fig2)

    # Bugs per Assignee
    st.subheader("Bugs per Assignee")
    fig3, ax3 = plt.subplots(figsize=(10,4))
    df_filtered[df_filtered['Is Bug']].groupby('Assignee')['ID'].count().plot(kind='bar', color='red', ax=ax3)
    st.pyplot(fig3)

    # Completion Time Distribution
    st.subheader("Completion Time Distribution by Category")
    fig4, ax4 = plt.subplots(figsize=(10,4))
    df_filtered.boxplot(column='Completion Time (days)', by='Task Category', ax=ax4)
    ax4.set_title("Completion Time by Category")
    ax4.set_xlabel("Category")
    ax4.set_ylabel("Days")
    st.pyplot(fig4)

    # Late Tasks
    st.subheader("Late Tasks per Category")
    fig5, ax5 = plt.subplots(figsize=(8,4))
    df_filtered[df_filtered['Is Late']].groupby('Task Category')['ID'].count().plot(kind='bar', color='orange', ax=ax5)
    st.pyplot(fig5)

    # Task Table
    st.subheader("Tasks Table")
    st.dataframe(df_filtered[['ID','Task','Assignee','Task Category','Status','Deadline','Completion Time (days)','Is Late']])