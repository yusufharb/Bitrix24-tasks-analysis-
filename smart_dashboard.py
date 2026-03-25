import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

st.set_page_config(layout="wide")
st.title("🚀 Smart Project Dashboard (Pro)")

# -------------------------
# Bitrix Fetch Function
# -------------------------
def fetch_bitrix_tasks(webhook_url):
    tasks = []
    start = 0

    while True:
        url = f"{webhook_url}?start={start}"
        response = requests.get(url).json()

        data = response.get('result', {}).get('tasks', [])
        tasks.extend(data)

        if 'next' in response:
            start = response['next']
        else:
            break

    return tasks

# -------------------------
# Convert to DataFrame
# -------------------------
def tasks_to_df(tasks):
    records = []

    for t in tasks:
        records.append({
            'ID': t['id'],
            'Task': t['title'],
            'Created by': t['createdBy']['name'],
            'Assignee': t['responsible']['name'],
            'Status': str(t['status']),
            'Created on': t['createdDate'],
            'Completed on': t.get('closedDate'),
            'Deadline': t.get('deadline'),
            'Project': t.get('group', {}).get('name', 'No Project')
        })

    return pd.DataFrame(records)

# -------------------------
# Sidebar: Data Source
# -------------------------
st.sidebar.header("📥 Data Source")

data_source = st.sidebar.radio(
    "Choose Data Source",
    ["Upload CSV", "Bitrix API"]
)

# -------------------------
# Load Data
# -------------------------
df = None

if data_source == "Upload CSV":
    file = st.sidebar.file_uploader("Upload CSV", type="csv")
    if file:
        df = pd.read_csv(file)

elif data_source == "Bitrix API":
    webhook = st.sidebar.text_input("Enter Inbound Webhook URL")
    if webhook:
        tasks = fetch_bitrix_tasks(webhook)
        df = tasks_to_df(tasks)

if df is None:
    st.info("👆 Upload data or connect Bitrix")
    st.stop()

# -------------------------
# Data Cleaning
# -------------------------
for col in ['Created on','Completed on','Deadline']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# -------------------------
# Multi-Project Filter 🔥
# -------------------------
st.sidebar.header("📁 Project Filter")

projects = df['Project'].dropna().unique()
selected_projects = st.sidebar.multiselect(
    "Select Projects",
    projects,
    default=projects
)

df = df[df['Project'].isin(selected_projects)]

# -------------------------
# Roles Config
# -------------------------
st.sidebar.header("⚙️ Roles")

all_users = pd.concat([df['Created by'], df['Assignee']]).dropna().unique()

testers = st.sidebar.multiselect("Testers", all_users)
frontend = st.sidebar.multiselect("Frontend", all_users)
backend = st.sidebar.multiselect("Backend", all_users)

# -------------------------
# Categorization
# -------------------------
def categorize(row):
    if row['Created by'] in testers:
        return 'Bug'
    elif row['Assignee'] in frontend:
        return 'Frontend'
    elif row['Assignee'] in backend:
        return 'Backend'
    else:
        return 'Other'

df['Task Category'] = df.apply(categorize, axis=1)
df['Is Bug'] = df['Created by'].isin(testers)
df['Is Completed'] = df['Status'].str.contains('5|complete', case=False, na=False)

# -------------------------
# Overview
# -------------------------
st.header("📊 Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Tasks", len(df))
col2.metric("Completed", df['Is Completed'].sum())
col3.metric("Bugs", df['Is Bug'].sum())

# Pie
fig = px.pie(df, names='Task Category', title="Tasks Distribution")
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Tasks per Assignee
# -------------------------
fig = px.bar(
    df['Assignee'].value_counts().reset_index(),
    x='Assignee',
    y='count',
    title="Tasks per Assignee"
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Bugs per Assignee
# -------------------------
bugs_df = df[df['Is Bug']]

fig = px.bar(
    bugs_df['Assignee'].value_counts().reset_index(),
    x='Assignee',
    y='count',
    title="Bugs per Assignee",
    color_discrete_sequence=['red']
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Burndown Chart
# -------------------------
st.header("📉 Burndown")

start = df['Created on'].min()
end = df['Completed on'].max()

days = pd.date_range(start=start, end=end)

remaining = [df[df['Completed on'] > d].shape[0] for d in days]

burndown_df = pd.DataFrame({
    'Date': days,
    'Remaining': remaining
})

fig = px.line(burndown_df, x='Date', y='Remaining', title="Burndown Chart")
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Velocity
# -------------------------
st.header("🚀 Team Velocity")

df_completed = df[df['Is Completed']]

if not df_completed.empty:
    velocity = df_completed.groupby(
        df_completed['Completed on'].dt.to_period('W')
    ).size()

    velocity_df = velocity.reset_index()
    velocity_df.columns = ['Week', 'Tasks']
    velocity_df['Week'] = velocity_df['Week'].astype(str)

    fig = px.line(velocity_df, x='Week', y='Tasks', markers=True, title="Velocity")
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Table
# -------------------------
st.header("📄 Data")
st.dataframe(df)