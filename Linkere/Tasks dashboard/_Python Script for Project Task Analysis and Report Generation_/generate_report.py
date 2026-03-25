
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import warnings
import numpy as np
import os

# Suppress warnings for HTML parsing
warnings.filterwarnings("ignore", category=UserWarning)

# --- Configuration ---
FILE_PATH = '/home/ubuntu/upload/tasksonbitrix24.xls'
REPORT_START_DATE = pd.to_datetime('2026-02-18')
REPORT_END_DATE = pd.to_datetime('2026-03-18')
REPORT_TITLE = f"Project Report – Linkere | {REPORT_START_DATE.strftime('%b %d')} – {REPORT_END_DATE.strftime('%b %d')}, {REPORT_END_DATE.year}"
OUTPUT_PDF_NAME = f"Project_Report_Linkere_{REPORT_START_DATE.strftime('%b%d')}_{REPORT_END_DATE.strftime('%b%d')}_{REPORT_END_DATE.year}.pdf"

# Ensure output directories exist
if not os.path.exists('plots'):
    os.makedirs('plots')

# --- 1. LOAD & CLEAN ---
def load_and_clean_data(file_path):
    df = pd.read_html(file_path, encoding='utf-8')[0]

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Date columns to parse
    date_cols = ['Created on', 'Deadline', 'Completed on', 'Start date', 'Modified on']
    for col in date_cols:
        if col in df.columns:
            # Replace 'nan' string with actual NaN and then parse dates
            df[col] = df[col].replace('nan', np.nan)
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().replace('nan', np.nan) # Convert to string before stripping

    return df

# --- 2. FILTER ---
def filter_data(df, start_date, end_date):
    if 'Created on' in df.columns:
        df_filtered = df[(df['Created on'] >= start_date) & (df['Created on'] <= end_date)].copy()
    else:
        df_filtered = df.copy()
    return df_filtered

# --- 3. CATEGORIZE ---
def categorize_tasks(df):
    df['Task Category'] = df['Created by'].apply(lambda x: 'Bug' if x in ['Yara Mahmoud', 'Muhammed Talaat'] else 'Regular Task')
    return df

# --- 4. DASHBOARD (print to console) ---
def generate_dashboard(df):
    print("\n--- Dashboard ---")

    # Status breakdown
    status_breakdown = df['Status'].value_counts(dropna=False)
    status_percentage = df['Status'].value_counts(normalize=True, dropna=False) * 100
    print("\nStatus Breakdown:")
    print(pd.DataFrame({"Count": status_breakdown, "Percentage": status_percentage.round(2).astype(str) + '%'}))

    # Tasks per Assignee with status breakdown
    tasks_per_assignee_status = df.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
    print("\nTasks per Assignee by Status:")
    print(tasks_per_assignee_status)

    # Tasks per Category
    tasks_per_category = df['Task Category'].value_counts()
    print("\nTasks per Category:")
    print(tasks_per_category)

    # Tasks with no deadline
    no_deadline_tasks = df[df['Deadline'].isna()]
    print(f"\nTasks with no deadline: {len(no_deadline_tasks)}")

    # Overdue tasks
    today = pd.to_datetime(datetime.now().date())
    # Ensure 'Completed' status is handled, even if not present in this specific export
    overdue_tasks = df[(df['Deadline'] < today) & (df['Status'] != 'Completed')]
    print(f"\nOverdue tasks (Deadline < {today.strftime('%Y-%m-%d')} and Status != Completed): {len(overdue_tasks)}")
    return status_breakdown, tasks_per_assignee_status, tasks_per_category, no_deadline_tasks, overdue_tasks

# --- 5. VISUALIZATIONS (save as PNG) ---
def generate_visualizations(df):
    print("\n--- Generating Visualizations ---")
    plt.style.use('seaborn-v0_8-darkgrid')

    # 5.1 Pie chart: Status distribution
    plt.figure(figsize=(8, 8))
    status_counts = df['Status'].value_counts()
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('Task Status Distribution')
    plt.axis('equal')
    plt.savefig('plots/status_distribution_pie.png')
    plt.close()

    # 5.2 Stacked bar: Tasks per Assignee by Status
    plt.figure(figsize=(12, 7))
    tasks_per_assignee_status = df.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
    tasks_per_assignee_status.plot(kind='bar', stacked=True, colormap='viridis')
    plt.title('Tasks per Assignee by Status')
    plt.xlabel('Assignee')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('plots/assignee_status_stacked_bar.png')
    plt.close()

    # 5.3 Horizontal bar: Tasks per Assignee colored by Category
    plt.figure(figsize=(12, 7))
    assignee_category_counts = df.groupby(['Assignee', 'Task Category']).size().unstack(fill_value=0)
    assignee_category_counts.plot(kind='barh', stacked=True, colormap='plasma')
    plt.title('Tasks per Assignee by Category')
    plt.xlabel('Number of Tasks')
    plt.ylabel('Assignee')
    plt.tight_layout()
    plt.savefig('plots/assignee_category_horizontal_bar.png')
    plt.close()

    # 5.4 Bar chart: Bug vs Regular Task count
    plt.figure(figsize=(8, 6))
    df['Task Category'].value_counts().plot(kind='bar', color=['skyblue', 'lightcoral'])
    plt.title('Bug vs Regular Task Count')
    plt.xlabel('Task Category')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('plots/bug_regular_task_bar.png')
    plt.close()

    # 5.5 Heatmap: Assignee vs Status
    plt.figure(figsize=(12, 8))
    heatmap_data = df.groupby(['Assignee', 'Status']).size().unstack(fill_value=0)
    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5)
    plt.title('Heatmap of Assignee vs Status')
    plt.xlabel('Status')
    plt.ylabel('Assignee')
    plt.tight_layout()
    plt.savefig('plots/assignee_status_heatmap.png')
    plt.close()
    print("Visualizations saved to 'plots/' directory.")

# --- 6. PDF REPORT ---
def create_pdf_report(df, status_breakdown, tasks_per_assignee_status, tasks_per_category, no_deadline_tasks, overdue_tasks, output_filename, report_title):
    print("\n--- Generating PDF Report ---")
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Cover Page
    story.append(Paragraph('<font size="24"><b>' + report_title + '</b></font>', styles['h1']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Generated by Manus AI", styles['Normal']))
    story.append(PageBreak())

    # Helper for adding tables
    def add_table(title, data_df, col_widths=None):
        story.append(Paragraph('<font size="16"><b>' + title + '</b></font>', styles['h2']))
        story.append(Spacer(1, 0.1 * inch))
        data = [data_df.columns.tolist()] + data_df.values.tolist()
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    # Section 1: Executive Summary Table
    total_tasks = len(df)
    completed_tasks = df[df['Status'] == 'Completed'].shape[0]
    in_progress_tasks = df[df['Status'] == 'In Progress'].shape[0]
    pending_tasks = df[df['Status'] == 'Pending'].shape[0]
    bug_tasks = df[df['Task Category'] == 'Bug'].shape[0]
    regular_tasks = df[df['Task Category'] == 'Regular Task'].shape[0]

    executive_summary_data = {
        'Metric': ['Total Tasks', 'Completed Tasks', 'In Progress Tasks', 'Pending Tasks', '"Bug" Tasks', '"Regular" Tasks', 'Tasks with No Deadline', 'Overdue Tasks'],
        'Value': [total_tasks, completed_tasks, in_progress_tasks, pending_tasks, bug_tasks, regular_tasks, len(no_deadline_tasks), len(overdue_tasks)]
    }
    executive_summary_df = pd.DataFrame(executive_summary_data)
    add_table("1. Executive Summary", executive_summary_df, col_widths=[2.5*inch, 1.5*inch])
    story.append(PageBreak())

    # Section 2: Status Breakdown Table
    status_breakdown_df = pd.DataFrame({
        'Status': status_breakdown.index,
        'Count': status_breakdown.values,
        'Percentage': (status_breakdown / total_tasks * 100).round(2).astype(str) + '%'
    })
    add_table("2. Status Breakdown", status_breakdown_df, col_widths=[2*inch, 1*inch, 1*inch])
    story.append(PageBreak())

    # Section 3: Assignee Performance Table
    add_table("3. Assignee Performance by Status", tasks_per_assignee_status)
    story.append(PageBreak())

    # Section 4: Bug Tasks Table
    bug_tasks_df = df[df['Task Category'] == 'Bug'][['Task', 'Assignee', 'Status', 'Created on', 'Deadline']]
    bug_tasks_df['Created on'] = bug_tasks_df['Created on'].dt.strftime('%Y-%m-%d')
    bug_tasks_df['Deadline'] = bug_tasks_df['Deadline'].dt.strftime('%Y-%m-%d')
    add_table("4. Bug Tasks (Created by Yara Mahmoud or Muhammed Talaat)", bug_tasks_df, col_widths=[2.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
    story.append(PageBreak())

    # Section 5: Regular Tasks Table
    regular_tasks_df = df[df['Task Category'] == 'Regular Task'][['Task', 'Assignee', 'Status', 'Created on', 'Deadline']]
    regular_tasks_df['Created on'] = regular_tasks_df['Created on'].dt.strftime('%Y-%m-%d')
    regular_tasks_df['Deadline'] = regular_tasks_df['Deadline'].dt.strftime('%Y-%m-%d')
    add_table("5. Regular Tasks", regular_tasks_df, col_widths=[2.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
    story.append(PageBreak())

    # Section 6: All 5 Plots Embedded
    story.append(Paragraph('<font size="16"><b>6. Visualizations</b></font>', styles['h2']))
    story.append(Spacer(1, 0.1 * inch))
    plot_files = [
        'plots/status_distribution_pie.png',
        'plots/assignee_status_stacked_bar.png',
        'plots/assignee_category_horizontal_bar.png',
        'plots/bug_regular_task_bar.png',
        'plots/assignee_status_heatmap.png'
    ]
    for plot_file in plot_files:
        if os.path.exists(plot_file):
            img = Image(plot_file, width=6*inch, height=4.5*inch) # Adjust size as needed
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))
        else:
            story.append(Paragraph(f"Image not found: {plot_file}", styles['Normal']))
    story.append(PageBreak())

    # Section 7: Key Insights (auto-generated)
    story.append(Paragraph('<font size="16"><b>7. Key Insights</b></font>', styles['h2']))
    story.append(Spacer(1, 0.1 * inch))

    # Insight 1: Overall Status
    most_common_status = status_breakdown.index[0]
    most_common_status_count = status_breakdown.iloc[0]
    story.append(Paragraph(f"- The most prevalent task status is \'{most_common_status}\' with {most_common_status_count} tasks, indicating a significant portion of work in this stage.", styles['Normal']))

    # Insight 2: Assignee workload
    if not tasks_per_assignee_status.empty:
        total_tasks_per_assignee = tasks_per_assignee_status.sum(axis=1)
        busiest_assignee = total_tasks_per_assignee.idxmax()
        busiest_assignee_tasks = total_tasks_per_assignee.max()
        story.append(Paragraph(f"- \'{busiest_assignee}\' appears to be the busiest assignee, handling {busiest_assignee_tasks} tasks during this period.", styles['Normal']))

    # Insight 3: Bug vs Regular Tasks
    if 'Bug' in tasks_per_category and 'Regular Task' in tasks_per_category:
        bug_count = tasks_per_category['Bug']
        regular_count = tasks_per_category['Regular Task']
        if bug_count > regular_count:
            story.append(Paragraph(f"- There are {bug_count} 'Bug' tasks compared to {regular_count} 'Regular Tasks', suggesting a higher focus on addressing issues during this period.", styles['Normal']))
        else:
            story.append(Paragraph(f"- There are {regular_count} 'Regular Tasks' compared to {bug_count} 'Bug' tasks, indicating a steady flow of new development or operational work.", styles['Normal']))

    # Insight 4: Tasks without deadlines
    if len(no_deadline_tasks) > 0:
        story.append(Paragraph(f"- A total of {len(no_deadline_tasks)} tasks currently lack a defined deadline, which could lead to potential delays or missed targets if not addressed.", styles['Normal']))

    # Insight 5: Overdue tasks
    if len(overdue_tasks) > 0:
        story.append(Paragraph(f"- There are {len(overdue_tasks)} overdue tasks, highlighting areas that require immediate attention to prevent further project slippage.", styles['Normal']))

    # Build PDF with page numbers
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(letter[0] / 2.0, 0.75 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF report saved as {output_filename}")

# --- Main Execution ---
if __name__ == "__main__":
    df_raw = load_and_clean_data(FILE_PATH)
    df_filtered = filter_data(df_raw, REPORT_START_DATE, REPORT_END_DATE)
    df_categorized = categorize_tasks(df_filtered)

    status_breakdown, tasks_per_assignee_status, tasks_per_category, no_deadline_tasks, overdue_tasks = generate_dashboard(df_categorized)
    generate_visualizations(df_categorized)
    create_pdf_report(df_categorized, status_breakdown, tasks_per_assignee_status, tasks_per_category, no_deadline_tasks, overdue_tasks, OUTPUT_PDF_NAME, REPORT_TITLE)

