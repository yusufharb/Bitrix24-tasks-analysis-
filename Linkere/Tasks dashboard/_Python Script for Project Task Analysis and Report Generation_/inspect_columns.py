import pandas as pd
import warnings

# Suppress warnings for HTML parsing
warnings.filterwarnings("ignore", category=UserWarning)

try:
    # Load the file as an HTML table as specified by the user
    df = pd.read_html('/home/ubuntu/upload/tasksonbitrix24.xls', encoding='utf-8')[0]
    print("Columns found in the file:")
    print(df.columns.tolist())
    print("\nFirst 5 rows of key columns (if they exist):")
    key_cols = ['Created on', 'Deadline', 'Completed on', 'Start date', 'Modified on', 'Assignee', 'Created by', 'Status']
    existing_key_cols = [col for col in key_cols if col in df.columns]
    print(df[existing_key_cols].head())
except Exception as e:
    print(f"Error: {e}")
