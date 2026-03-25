import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json

# -------------------------
# Page Setup
# -------------------------
st.set_page_config(layout="wide")
st.title("🚀 Smart Project Dashboard System")

# -------------------------
# Upload Files
# -------------------------
csv_file = st.file_uploader("Upload Tasks CSV", type="csv")
config_file = st.file_uploader("Upload Config JSON (optional)", type="json")

if not csv_file:
    st.info("👆 Upload a CSV file to start the dashboard")
    st.stop()

# -------------------------
# Load Data
# -------------------------
df = pd.read_csv(csv_file)

# -------------------------
# Load Config
# -------------------------
if config_file:
    roles = json.load(config_file)
else:
    roles = {
        "testers": [],
        "regular_creators": [],
        "frontend_team": [],
        "backend_team": []
    }

# -------------------------
# Dynamic Role Selection UI
# -------------------------
st.sidebar.header("⚙️ Define Team Roles")

all_users = pd.concat([df['Created by'], df['Assignee']]).dropna().unique()

roles['testers'] = st.sidebar.multiselect("Testers (Bug creators)", all_users, default=roles['testers'])
roles['regular_creators'] = st.sidebar.multiselect("Regular Task Creators", all_users, default=roles['regular_creators'])
roles['frontend_team'] = st.sidebar.multiselect("Frontend Team", all_users, default=roles['frontend_team'])
roles['backend_team'] = st.sidebar.multiselect("Backend Team", all_users, default=roles['backend_team'])

# -------------------------
# Data Cleaning
# -------------------------
date_cols = ['Created on','Completed on','Deadline']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# -------------------------
# Categorization
# -------------------------
def categorize_task(row):
    if row['Created by'] in roles['testers']:
        return 'Bug'
    elif row['Created by'] in roles['regular_creators']:
        return 'Regular Task'
    elif row['Assignee'] in roles['frontend_team']:
        return 'Frontend Task'
    elif row['Assignee'] in roles['backend_team']:
        return 'Backend Task'
    else:
        return 'Other'

df['Task Category'] = df.apply(categorize_task, axis=1)
df['Is Bug'] = df['Created by'].isin(roles['testers'])
df['Is Completed'] = df['Status'].astype(str).str.lower().str.contains('complete', na=False)
df['Completion Time'] = (df['Completed on'] - df['Created on']).dt.days
df['Is Late'] = df['Completed on'] > df['Deadline']

# -------------------------
# Filters
# -------------------------
st.sidebar.header("📊 Filters")

assignee_filter = st.sidebar.multiselect(
    "Assignee",
    df['Assignee'].dropna().unique(),
    default=df['Assignee'].dropna().unique()
)

df_filtered = df[df['Assignee'].isin(assignee_filter)]

# -------------------------
# Overview
# -------------------------
st.header("📊 Overview")

col1, col2, col3, col4 = st.columns(4)

total = len(df_filtered)
completed = df_filtered['Is Completed'].sum()
bugs = df_filtered['Is Bug'].sum()
rate = (completed / total * 100) if total > 0 else 0

col1.metric("Total Tasks", total)
col2.metric("Completed", completed)
col3.metric("Completion %", f"{rate:.1f}%")
col4.metric("Bugs", bugs)

# Pie Chart
fig1, ax1 = plt.subplots()
df_filtered['Task Category'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax1)
ax1.set_ylabel("")
st.pyplot(fig1)

# -------------------------
# Detailed Analysis
# -------------------------
st.header("📋 Detailed Analysis")

# Tasks per Assignee
fig2, ax2 = plt.subplots(figsize=(10,4))
df_filtered['Assignee'].value_counts().plot(kind='bar', ax=ax2)
ax2.set_title("Tasks per Assignee")
st.pyplot(fig2)

# Bugs per Assignee
fig3, ax3 = plt.subplots(figsize=(10,4))
df_filtered[df_filtered['Is Bug']].groupby('Assignee')['ID'].count().plot(kind='bar', ax=ax3)
ax3.set_title("Bugs per Assignee")
st.pyplot(fig3)

# -------------------------
# Burndown Chart
# -------------------------
st.header("📉 Burndown Chart")

min_date = df['Created on'].min().date()
max_date = df['Completed on'].max().date()

start_date, end_date = st.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

days = pd.date_range(start=start_date, end=end_date)

remaining = []
for day in days:
    remaining.append(df[df['Completed on'] > day].shape[0])

fig4, ax4 = plt.subplots(figsize=(12,5))
ax4.plot(days, remaining, marker='o', label='Actual')

if len(remaining) > 0:
    ideal = [remaining[0] - i*(remaining[0]/(len(days)-1)) for i in range(len(days))]
    ax4.plot(days, ideal, linestyle='--', label='Ideal')

ax4.set_title("Burndown Chart")
ax4.legend()
ax4.grid()

st.pyplot(fig4)

# -------------------------
# Team Velocity
# -------------------------
st.header("🚀 Team Velocity")

df_completed = df_filtered[df_filtered['Is Completed'] == True]

if not df_completed.empty:

    velocity = df_completed.groupby(
        df_completed['Completed on'].dt.to_period('W')
    ).size()

    velocity_df = velocity.reset_index()
    velocity_df.columns = ['Week', 'Completed Tasks']
    velocity_df['Week'] = velocity_df['Week'].astype(str)

    fig5, ax5 = plt.subplots(figsize=(10,4))
    ax5.plot(velocity_df['Week'], velocity_df['Completed Tasks'], marker='o')

    ax5.set_title("Team Velocity (Weekly)")
    ax5.set_xlabel("Week")
    ax5.set_ylabel("Tasks")
    ax5.grid(True)

    plt.xticks(rotation=45)
    st.pyplot(fig5)

    # Velocity per Category
    st.subheader("Velocity by Task Category")

    velocity_team = df_completed.groupby(
        [df_completed['Completed on'].dt.to_period('W'), 'Task Category']
    ).size().unstack(fill_value=0)

    velocity_team.index = velocity_team.index.astype(str)

    fig6, ax6 = plt.subplots(figsize=(12,5))
    velocity_team.plot(ax=ax6, marker='o')

    ax6.grid(True)
    plt.xticks(rotation=45)

    st.pyplot(fig6)

else:
    st.warning("No completed tasks available for velocity calculation")

# -------------------------
# Data Table
# -------------------------
st.header("📄 Data Table")
st.dataframe(df_filtered)