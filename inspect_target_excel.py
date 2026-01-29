import pandas as pd

try:
    file_path = "output/redding_jobs_20260129_095105.xlsx"
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    if not df.empty:
        print("\nSource Counts:")
        print(df['source'].value_counts())
        
        snag_df = df[df['source'] == 'Snagajob']
        if not snag_df.empty:
            print("\nSample Snagajob Row:")
            print(snag_df.iloc[0].to_dict())
        else:
            print("\nNo Snagajob jobs found.")
except Exception as e:
    print(f"Error reading excel: {e}")
