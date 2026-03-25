import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, Image as RLImage,
                                 HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─────────────────────────────────────────────
# STEP 1 — LOAD & CLEAN
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Loading & Cleaning Data")
print("=" * 60)

df = pd.read_html('/mnt/user-data/uploads/tasks_2026-03-18_11-45-53.xls', encoding='utf-8')[0]
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

# Parse date columns
date_cols = ['Created on', 'Deadline', 'Completed on', 'Start date', 'Modified on']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Strip whitespace from string columns
str_cols = df.select_dtypes(include='object').columns
for col in str_cols:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace('nan', pd.NA)

print("Data cleaned successfully.\n")

# ─────────────────────────────────────────────
# STEP 2 — FILTER Feb 18 → Mar 18, 2026
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 2: Filtering Feb 18 – Mar 18, 2026")
print("=" * 60)

start_date = pd.Timestamp('2026-02-18')
end_date   = pd.Timestamp('2026-03-18 23:59:59')
df_filtered = df[(df['Created on'] >= start_date) & (df['Created on'] <= end_date)].copy()

print(f"Tasks in range: {len(df_filtered)}")
print("\nTasks per Assignee in range:")
print(df_filtered['Assignee'].value_counts().to_string())
print()

# ─────────────────────────────────────────────
# STEP 3 — CATEGORISATION
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 3: Task Categorisation")
print("=" * 60)

def categorise(assignee):
    if assignee == 'Yara Mahmoud':
        return 'Bug'
    elif assignee == 'Ahmed Abdelfattah':
        return 'Regular Task'
    else:
        return 'General'

df_filtered['Task Category'] = df_filtered['Assignee'].apply(categorise)
print(df_filtered['Task Category'].value_counts().to_string())
print()

# ─────────────────────────────────────────────
# STEP 4 — DASHBOARD SUMMARY
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 4: Dashboard Summary")
print("=" * 60)

today = pd.Timestamp('2026-03-18')

# Status totals
status_counts = df_filtered['Status'].value_counts()
total = len(df_filtered)
print("\n── Status Breakdown ──")
for s, c in status_counts.items():
    print(f"  {s:15s}: {c:3d}  ({c/total*100:.1f}%)")

# Per-assignee breakdown
print("\n── Per-Assignee Breakdown ──")
assignee_stats = df_filtered.groupby('Assignee')['Status'].value_counts().unstack(fill_value=0)
for col in ['Completed', 'In Progress', 'Pending']:
    if col not in assignee_stats:
        assignee_stats[col] = 0
assignee_stats['Total'] = assignee_stats.sum(axis=1)
assignee_stats['Completion %'] = (assignee_stats.get('Completed', 0) / assignee_stats['Total'] * 100).round(1)
print(assignee_stats.to_string())

# Category breakdown
print("\n── Category Breakdown ──")
print(df_filtered['Task Category'].value_counts().to_string())

# Overall completion
overall_pct = status_counts.get('Completed', 0) / total * 100
print(f"\n── Overall Completion Rate: {overall_pct:.1f}% ──")

# Avg time to complete
completed = df_filtered[df_filtered['Status'] == 'Completed'].copy()
completed['Duration'] = (completed['Completed on'] - completed['Created on']).dt.days
avg_days = completed['Duration'].dropna().mean()
print(f"── Avg days to complete (Completed tasks): {avg_days:.1f} days ──")

# Tasks with no deadline
no_deadline = df_filtered['Deadline'].isna().sum()
print(f"── Tasks with no deadline: {no_deadline} ──")

# Overdue tasks
overdue = df_filtered[(df_filtered['Deadline'] < today) &
                       (df_filtered['Status'] != 'Completed') &
                       (df_filtered['Deadline'].notna())]
print(f"── Overdue tasks: {len(overdue)} ──\n")

# ─────────────────────────────────────────────
# STEP 5 — VISUALISATIONS
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 5: Generating Plots")
print("=" * 60)

PALETTE = {
    'Completed':   '#2ecc71',
    'In Progress': '#f39c12',
    'Pending':     '#e74c3c',
    'Bug':         '#9b59b6',
    'Regular Task':'#3498db',
    'General':     '#95a5a6',
}
ACCENT   = '#2c3e50'
BG_COLOR = '#fafafa'

# Helper
def save_fig(fig, filename):
    fig.savefig(f'/home/claude/{filename}', bbox_inches='tight', dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Saved {filename}")

# ── Plot 1: Pie – Status Distribution ──
fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG_COLOR)
labels = status_counts.index.tolist()
sizes  = status_counts.values
pie_colors = [PALETTE.get(l, '#bdc3c7') for l in labels]
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                   colors=pie_colors, startangle=140,
                                   wedgeprops=dict(edgecolor='white', linewidth=2))
for at in autotexts:
    at.set_fontsize(11); at.set_fontweight('bold'); at.set_color('white')
ax.set_title('Overall Task Status Distribution\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT, pad=15)
save_fig(fig, 'plot_01_status_distribution.png')

# ── Plot 2: Stacked Bar – Tasks per Assignee by Status ──
fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG_COLOR)
pivot = df_filtered.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
for col in ['Completed', 'In Progress', 'Pending']:
    if col not in pivot: pivot[col] = 0
pivot = pivot[['Completed', 'In Progress', 'Pending']]
bottom = np.zeros(len(pivot))
for status in ['Completed', 'In Progress', 'Pending']:
    ax.bar(pivot.index, pivot[status], bottom=bottom,
           label=status, color=PALETTE[status], edgecolor='white', linewidth=0.8)
    bottom += pivot[status].values
ax.set_xlabel('Assignee', fontsize=11)
ax.set_ylabel('Number of Tasks', fontsize=11)
ax.set_title('Tasks per Assignee (Stacked by Status)\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT)
ax.legend(title='Status', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.xticks(rotation=30, ha='right', fontsize=9)
ax.set_facecolor(BG_COLOR); ax.grid(axis='y', alpha=0.3)
save_fig(fig, 'plot_02_tasks_per_assignee.png')

# ── Plot 3: Horizontal Bar – Completion Rate per Assignee ──
fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG_COLOR)
comp_rate = assignee_stats['Completion %'].sort_values(ascending=True)
bar_colors = ['#2ecc71' if v >= 80 else '#f39c12' if v >= 50 else '#e74c3c' for v in comp_rate]
bars = ax.barh(comp_rate.index, comp_rate.values, color=bar_colors, edgecolor='white', height=0.6)
for bar, val in zip(bars, comp_rate.values):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{val:.0f}%', va='center', ha='left', fontsize=10, fontweight='bold')
ax.set_xlabel('Completion Rate (%)', fontsize=11)
ax.set_title('Task Completion Rate per Assignee\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT)
ax.set_xlim(0, 115)
ax.axvline(x=80, color='gray', linestyle='--', alpha=0.5, label='80% target')
ax.legend(); ax.set_facecolor(BG_COLOR); ax.grid(axis='x', alpha=0.3)
save_fig(fig, 'plot_03_completion_rate.png')

# ── Plot 4: Bar – Category Breakdown ──
fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG_COLOR)
cat_counts = df_filtered['Task Category'].value_counts()
cat_colors = [PALETTE.get(c, '#bdc3c7') for c in cat_counts.index]
bars = ax.bar(cat_counts.index, cat_counts.values, color=cat_colors, edgecolor='white', width=0.5)
for bar, val in zip(bars, cat_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
            str(val), ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of Tasks', fontsize=11)
ax.set_title('Task Category Breakdown\n(Bug / Regular Task / General)',
             fontsize=14, fontweight='bold', color=ACCENT)
ax.set_facecolor(BG_COLOR); ax.grid(axis='y', alpha=0.3)
save_fig(fig, 'plot_04_category_breakdown.png')

# ── Plot 5: Line – Tasks Created per Week ──
fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
df_filtered['Week'] = df_filtered['Created on'].dt.to_period('W').apply(lambda r: r.start_time)
weekly = df_filtered.groupby('Week').size().reset_index(name='Count')
ax.plot(weekly['Week'], weekly['Count'], marker='o', linewidth=2.5,
        color='#3498db', markerfacecolor='white', markeredgewidth=2, markersize=8)
ax.fill_between(weekly['Week'], weekly['Count'], alpha=0.15, color='#3498db')
for _, row in weekly.iterrows():
    ax.text(row['Week'], row['Count'] + 0.3, str(int(row['Count'])),
            ha='center', va='bottom', fontsize=9)
ax.set_xlabel('Week Starting', fontsize=11)
ax.set_ylabel('Tasks Created', fontsize=11)
ax.set_title('Tasks Created per Week\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT)
plt.xticks(rotation=30, ha='right')
ax.set_facecolor(BG_COLOR); ax.grid(alpha=0.3)
save_fig(fig, 'plot_05_tasks_per_week.png')

# ── Plot 6: Heatmap – Assignee vs Status ──
fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG_COLOR)
heat_data = df_filtered.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
for col in ['Completed', 'In Progress', 'Pending']:
    if col not in heat_data: heat_data[col] = 0
heat_data = heat_data[['Completed', 'In Progress', 'Pending']]
sns.heatmap(heat_data, annot=True, fmt='d', cmap='YlOrRd', linewidths=0.5,
            linecolor='white', ax=ax, cbar_kws={'label': 'Task Count'})
ax.set_title('Assignee × Status Heatmap\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT, pad=12)
ax.set_xlabel('Status', fontsize=11)
ax.set_ylabel('Assignee', fontsize=11)
plt.yticks(rotation=0)
save_fig(fig, 'plot_06_heatmap.png')

# ── Plot 7: Bar – Completed Tasks per Week ──
fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
completed_only = df_filtered[df_filtered['Status'] == 'Completed'].copy()
completed_only['Week'] = completed_only['Created on'].dt.to_period('W').apply(lambda r: r.start_time)
weekly_comp = completed_only.groupby('Week').size().reset_index(name='Completed')
ax.bar(weekly_comp['Week'].astype(str), weekly_comp['Completed'],
       color='#2ecc71', edgecolor='white', width=0.6)
for i, (_, row) in enumerate(weekly_comp.iterrows()):
    ax.text(i, row['Completed'] + 0.3, str(int(row['Completed'])),
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_xlabel('Week Starting', fontsize=11)
ax.set_ylabel('Completed Tasks', fontsize=11)
ax.set_title('Completed Tasks per Week (Trend)\n(Feb 18 – Mar 18, 2026)',
             fontsize=14, fontweight='bold', color=ACCENT)
plt.xticks(rotation=30, ha='right')
ax.set_facecolor(BG_COLOR); ax.grid(axis='y', alpha=0.3)
save_fig(fig, 'plot_07_completed_per_week.png')

print("All 7 plots saved.\n")

# ─────────────────────────────────────────────
# STEP 6 — PDF REPORT
# ─────────────────────────────────────────────
print("=" * 60)
print("STEP 6: Generating PDF Report")
print("=" * 60)

PDF_PATH = '/home/claude/Project_Report_Linkere_Feb18_Mar18_2026.pdf'
doc = SimpleDocTemplate(PDF_PATH, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2.5*cm, bottomMargin=2*cm)

styles  = getSampleStyleSheet()
W, H    = A4

# Custom styles
def style(name, **kwargs):
    base = styles[name] if name in styles else styles['Normal']
    return ParagraphStyle(name + '_custom', parent=base, **kwargs)

s_title   = style('Title',    fontSize=26, textColor=colors.HexColor('#2c3e50'),
                   alignment=TA_CENTER, spaceAfter=10)
s_sub     = style('Normal',   fontSize=13, textColor=colors.HexColor('#7f8c8d'),
                   alignment=TA_CENTER, spaceAfter=6)
s_h1      = style('Heading1', fontSize=16, textColor=colors.HexColor('#2c3e50'),
                   spaceBefore=16, spaceAfter=6, borderPad=(0,0,4,0))
s_h2      = style('Heading2', fontSize=13, textColor=colors.HexColor('#3498db'),
                   spaceBefore=10, spaceAfter=4)
s_body    = style('Normal',   fontSize=10, leading=16, spaceAfter=4)
s_bullet  = style('Normal',   fontSize=10, leading=15, leftIndent=15, spaceAfter=3)

def divider(color='#bdc3c7'):
    return HRFlowable(width='100%', thickness=1, color=colors.HexColor(color), spaceAfter=10)

story = []

# ── Cover Page ──
story += [Spacer(1, 3*cm),
          Paragraph("Project Task Report", s_title),
          Paragraph("Linkere", style('Title', fontSize=32,
                                     textColor=colors.HexColor('#3498db'),
                                     alignment=TA_CENTER)),
          Spacer(1, 1*cm),
          divider('#3498db'),
          Spacer(1, 0.5*cm),
          Paragraph("Date Range: Feb 18, 2026 – Mar 18, 2026", s_sub),
          Paragraph(f"Generated: {date.today().strftime('%B %d, %Y')}", s_sub),
          Spacer(1, 4*cm),
          Paragraph("Prepared by: Project Analytics System", s_sub),
          PageBreak()]

# ── Section 1: Executive Summary ──
yara_total  = len(df_filtered[df_filtered['Assignee'] == 'Yara Mahmoud'])
ahmed_total = len(df_filtered[df_filtered['Assignee'] == 'Ahmed Abdelfattah'])

story += [Paragraph("1. Executive Summary", s_h1), divider(),
          Paragraph(f"This report covers <b>{total}</b> tasks created between "
                    f"<b>February 18, 2026</b> and <b>March 18, 2026</b> for the "
                    f"<b>Linkere</b> project.", s_body),
          Spacer(1, 0.3*cm)]

summary_data = [
    ['Metric', 'Value'],
    ['Total Tasks Analysed', str(total)],
    ['Overall Completion Rate', f'{overall_pct:.1f}%'],
    ['Completed Tasks', str(status_counts.get('Completed', 0))],
    ['In Progress Tasks', str(status_counts.get('In Progress', 0))],
    ['Pending Tasks', str(status_counts.get('Pending', 0))],
    ['Bug Tasks (Yara Mahmoud)', str(yara_total)],
    ['Regular Tasks (Ahmed Abdelfattah)', str(ahmed_total)],
    ['Tasks with No Deadline', str(no_deadline)],
    ['Overdue Tasks', str(len(overdue))],
    ['Avg Days to Complete', f'{avg_days:.1f} days'],
]
t = Table(summary_data, colWidths=[10*cm, 6*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0,0), (-1,-1), 10),
    ('ALIGN',      (1,0), (1,-1), 'CENTER'),
    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#eaf2ff')]),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ('ROUNDEDCORNERS', [4]),
    ('TOPPADDING',  (0,0), (-1,-1), 6),
    ('BOTTOMPADDING',(0,0), (-1,-1), 6),
]))
story += [t, PageBreak()]

# ── Section 2: Status Breakdown ──
story += [Paragraph("2. Status Breakdown", s_h1), divider()]
status_data = [['Status', 'Count', 'Percentage']]
for s in ['Completed', 'In Progress', 'Pending']:
    c = status_counts.get(s, 0)
    status_data.append([s, str(c), f'{c/total*100:.1f}%'])

t2 = Table(status_data, colWidths=[7*cm, 5*cm, 5*cm])
t2.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#27ae60')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0,0), (-1,-1), 11),
    ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#eafaf1')]),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ('TOPPADDING',  (0,0), (-1,-1), 8),
    ('BOTTOMPADDING',(0,0), (-1,-1), 8),
]))
story += [t2, Spacer(1, 0.5*cm),
          RLImage('/home/claude/plot_01_status_distribution.png', width=10*cm, height=7*cm),
          PageBreak()]

# ── Section 3: Assignee Performance ──
story += [Paragraph("3. Assignee Performance", s_h1), divider()]
perf_data = [['Assignee', 'Total', 'Completed', 'In Progress', 'Pending', 'Completion %']]
for assignee in assignee_stats.index:
    row = assignee_stats.loc[assignee]
    perf_data.append([
        assignee,
        str(int(row['Total'])),
        str(int(row.get('Completed', 0))),
        str(int(row.get('In Progress', 0))),
        str(int(row.get('Pending', 0))),
        f"{row['Completion %']:.1f}%"
    ])

t3 = Table(perf_data, colWidths=[4.5*cm, 2*cm, 2.5*cm, 2.8*cm, 2.2*cm, 3*cm])
t3.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2980b9')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0,0), (-1,-1), 9),
    ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#ebf5fb')]),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ('TOPPADDING',  (0,0), (-1,-1), 7),
    ('BOTTOMPADDING',(0,0), (-1,-1), 7),
]))
story += [t3, Spacer(1, 0.4*cm),
          RLImage('/home/claude/plot_02_tasks_per_assignee.png', width=16*cm, height=8*cm),
          Spacer(1, 0.3*cm),
          RLImage('/home/claude/plot_03_completion_rate.png', width=14*cm, height=8*cm),
          PageBreak()]

# ── Section 4: Bug Tasks – Yara Mahmoud ──
story += [Paragraph("4. Bug Tasks — Yara Mahmoud", s_h1), divider()]
yara_df = df_filtered[df_filtered['Assignee'] == 'Yara Mahmoud'][
    ['Task', 'Status', 'Created on', 'Deadline']].copy()

bug_data = [['Task Name', 'Status', 'Created On', 'Deadline']]
for _, row in yara_df.iterrows():
    task_name = str(row['Task'])[:50] + '...' if len(str(row['Task'])) > 50 else str(row['Task'])
    deadline  = row['Deadline'].strftime('%d %b %Y') if pd.notna(row['Deadline']) else '—'
    bug_data.append([task_name,
                     str(row['Status']),
                     row['Created on'].strftime('%d %b %Y'),
                     deadline])

t4 = Table(bug_data, colWidths=[8*cm, 2.8*cm, 3*cm, 3*cm])
t4.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8e44ad')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0,0), (-1,-1), 8),
    ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5eef8')]),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ('TOPPADDING',  (0,0), (-1,-1), 5),
    ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ('WORDWRAP',    (0,0), (-1,-1), True),
]))
story += [t4, PageBreak()]

# ── Section 5: Regular Tasks – Ahmed Abdelfattah ──
story += [Paragraph("5. Regular Tasks — Ahmed Abdelfattah", s_h1), divider()]
ahmed_df = df_filtered[df_filtered['Assignee'] == 'Ahmed Abdelfattah'][
    ['Task', 'Status', 'Created on', 'Deadline']].copy()

reg_data = [['Task Name', 'Status', 'Created On', 'Deadline']]
for _, row in ahmed_df.iterrows():
    task_name = str(row['Task'])[:50] + '...' if len(str(row['Task'])) > 50 else str(row['Task'])
    deadline  = row['Deadline'].strftime('%d %b %Y') if pd.notna(row['Deadline']) else '—'
    reg_data.append([task_name,
                     str(row['Status']),
                     row['Created on'].strftime('%d %b %Y'),
                     deadline])

t5 = Table(reg_data, colWidths=[8*cm, 2.8*cm, 3*cm, 3*cm])
t5.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2980b9')),
    ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
    ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0,0), (-1,-1), 8),
    ('ALIGN',      (1,0), (-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#ebf5fb')]),
    ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
    ('TOPPADDING',  (0,0), (-1,-1), 5),
    ('BOTTOMPADDING',(0,0), (-1,-1), 5),
]))
story += [t5, PageBreak()]

# ── Section 6: All Visualisations ──
story += [Paragraph("6. Visualisations", s_h1), divider()]

plots = [
    ('plot_04_category_breakdown.png',  'Category Breakdown'),
    ('plot_05_tasks_per_week.png',       'Tasks Created per Week'),
    ('plot_06_heatmap.png',              'Assignee × Status Heatmap'),
    ('plot_07_completed_per_week.png',   'Completed Tasks per Week'),
]
for fname, caption in plots:
    story.append(Paragraph(caption, s_h2))
    story.append(RLImage(f'/home/claude/{fname}', width=15*cm, height=9*cm))
    story.append(Spacer(1, 0.5*cm))

story.append(PageBreak())

# ── Section 7: Key Insights ──
story += [Paragraph("7. Key Insights &amp; Recommendations", s_h1), divider()]

best_assignee  = assignee_stats['Completion %'].idxmax()
worst_assignee = assignee_stats['Completion %'].idxmin()
best_pct       = assignee_stats.loc[best_assignee,  'Completion %']
worst_pct      = assignee_stats.loc[worst_assignee, 'Completion %']
pending_count  = status_counts.get('Pending', 0)

insights = [
    f"<b>High Overall Completion:</b> The team achieved a <b>{overall_pct:.1f}%</b> completion "
    f"rate across {total} tasks — indicating strong delivery in the Feb 18 – Mar 18 period.",

    f"<b>Top Performer:</b> <b>{best_assignee}</b> leads with a <b>{best_pct:.0f}%</b> completion rate, "
    f"demonstrating consistent task throughput.",

    f"<b>Needs Attention:</b> <b>{worst_assignee}</b> has the lowest completion rate at "
    f"<b>{worst_pct:.0f}%</b>. A workload review or additional support may be beneficial.",

    f"<b>Pending Backlog:</b> There are <b>{pending_count}</b> pending tasks still open. "
    f"Prioritising these in the next sprint will prevent accumulation.",

    f"<b>Bug Tracking (Yara Mahmoud):</b> <b>{yara_total}</b> tasks are categorised as bugs. "
    f"A dedicated bug-bash session is recommended if completion rate is below 80%.",

    f"<b>Deadline Coverage:</b> <b>{no_deadline}</b> tasks have no deadline assigned. "
    f"Setting deadlines will improve sprint planning and accountability.",

    f"<b>Average Cycle Time:</b> Completed tasks took an average of <b>{avg_days:.1f} days</b> "
    f"from creation to completion — a useful baseline for future estimation.",
]

for ins in insights:
    story.append(Paragraph(f"• {ins}", s_bullet))
    story.append(Spacer(1, 0.15*cm))

# ── Page numbers via onFirstPage / onLaterPages ──
def add_page_number(canvas_obj, doc_obj):
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#7f8c8d'))
    canvas_obj.drawRightString(A4[0] - 2*cm, 1.2*cm,
                                f"Page {doc_obj.page}  |  Linkere Project Report  |  Mar 2026")
    canvas_obj.restoreState()

doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

print(f"\nReport generated successfully: {PDF_PATH}")
