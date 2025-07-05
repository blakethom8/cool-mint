import pandas as pd
import os

def explore_excel_file(file_path):
    """
    Explore the structure of the Excel file to understand the data format
    """
    print(f"Exploring Excel file: {file_path}")
    print("=" * 50)
    
    try:
        # Read the Excel file
        if file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='xlrd')
        else:
            df = pd.read_excel(file_path)
        
        print(f"File shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print("\nColumn names:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        print(f"\nFirst 5 rows:")
        print(df.head())
        
        print(f"\nData types:")
        print(df.dtypes)
        
        # Look for any columns that might contain "Assigned" status
        print(f"\nLooking for columns that might contain assignment status...")
        for col in df.columns:
            if 'assign' in col.lower() or 'status' in col.lower():
                print(f"Potential assignment column: {col}")
                print(f"Unique values: {df[col].unique()}")
                print()
        
        # Show unique values for all columns with fewer than 20 unique values
        print(f"\nColumns with categorical data (< 20 unique values):")
        for col in df.columns:
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) < 20:
                print(f"{col}: {list(unique_vals)}")
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

if __name__ == "__main__":
    file_path = "report1749182913520.xls"
    
    if os.path.exists(file_path):
        df = explore_excel_file(file_path)
    else:
        print(f"File {file_path} not found in current directory")
        print("Available files:")
        for file in os.listdir('.'):
            if file.endswith(('.xls', '.xlsx')):
                print(f"  - {file}") 
                