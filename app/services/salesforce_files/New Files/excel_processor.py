import pandas as pd
import os
import chardet
from io import StringIO
from bs4 import BeautifulSoup

def process_html_excel_file(file_path):
    """
    Process the HTML-formatted Excel file and extract data
    """
    print(f"Processing HTML Excel file: {file_path}")
    print("=" * 50)
    
    try:
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result['encoding']
            print(f"Detected encoding: {detected_encoding}")
        
        # Try pandas read_html which is designed for HTML tables
        try:
            # Read HTML tables from file
            tables = pd.read_html(file_path, encoding=detected_encoding)
            print(f"Found {len(tables)} table(s)")
            
            if len(tables) > 0:
                df = tables[0]  # Use the first table
                print(f"Table shape: {df.shape[0]} rows, {df.shape[1]} columns")
                
                print(f"\nColumn names:")
                for i, col in enumerate(df.columns):
                    print(f"{i+1}. {col}")
                
                print(f"\nFirst 3 rows:")
                print(df.head(3))
                
                # Check for 'Assigned' column
                if 'Assigned' in df.columns:
                    print(f"\nUnique values in 'Assigned' column:")
                    assigned_counts = df['Assigned'].value_counts()
                    print(assigned_counts)
                    
                    return df, df.columns.tolist(), assigned_counts
                else:
                    print("\n'Assigned' column not found in the data")
                    print("Available columns:")
                    for col in df.columns:
                        print(f"  - {col}")
                    return df, df.columns.tolist(), None
            else:
                print("No tables found in the file")
                return None, None, None
                
        except Exception as e:
            print(f"pandas read_html failed: {str(e)}")
            # Fallback to manual parsing with different encodings
            return process_with_manual_parsing(file_path, detected_encoding)
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None, None, None

def process_with_manual_parsing(file_path, encoding):
    """
    Fallback method using manual HTML parsing
    """
    try:
        from bs4 import BeautifulSoup
        
        print("Trying manual HTML parsing...")
        
        # Try multiple encodings
        encodings_to_try = [encoding, 'latin1', 'cp1252', 'iso-8859-1']
        
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    content = f.read()
                print(f"Successfully read file with encoding: {enc}")
                break
            except:
                continue
        
        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the table
        table = soup.find('table')
        if not table:
            print("No table found in the file")
            return None, None, None
        
        # Extract headers
        headers = []
        header_row = table.find('tr')
        for th in header_row.find_all(['th', 'td']):  # Some files use td for headers
            headers.append(th.get_text().strip())
        
        print(f"Found {len(headers)} columns:")
        for i, header in enumerate(headers):
            print(f"{i+1}. {header}")
        
        # Extract data rows
        data_rows = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            row_data = []
            for td in row.find_all('td'):
                row_data.append(td.get_text().strip())
            if row_data and len(row_data) == len(headers):  # Only add complete rows
                data_rows.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        print(f"\nTotal records: {len(df)}")
        print(f"\nFirst 3 rows:")
        print(df.head(3))
        
        # Check for 'Assigned' column
        if 'Assigned' in df.columns:
            print(f"\nUnique values in 'Assigned' column:")
            assigned_counts = df['Assigned'].value_counts()
            print(assigned_counts)
            
            return df, headers, assigned_counts
        else:
            print("\n'Assigned' column not found in the data")
            return df, headers, None
        
    except Exception as e:
        print(f"Manual parsing also failed: {str(e)}")
        return None, None, None

def filter_by_assigned_user(df, assigned_user):
    """
    Filter the dataframe by assigned user
    """
    if df is None or 'Assigned' not in df.columns:
        return None
    
    filtered_df = df[df['Assigned'] == assigned_user].copy()
    print(f"\nFiltered data for '{assigned_user}': {len(filtered_df)} records")
    
    return filtered_df

def analyze_specialty_targeting(df, assigned_user):
    """
    Analyze what specialties the assigned user has been targeting
    """
    if df is None:
        return None
    
    filtered_df = filter_by_assigned_user(df, assigned_user)
    if filtered_df is None or len(filtered_df) == 0:
        return None
    
    print(f"\n=== ANALYSIS FOR {assigned_user.upper()} ===")
    
    # Analyze specialty groups
    if 'MN Specialty Group' in filtered_df.columns:
        specialty_counts = filtered_df['MN Specialty Group'].value_counts()
        print(f"\nSpecialties targeted:")
        for specialty, count in specialty_counts.items():
            print(f"  - {specialty}: {count} activities")
    
    # Analyze outreach types
    if 'Outreach Type' in filtered_df.columns:
        outreach_counts = filtered_df['Outreach Type'].value_counts()
        print(f"\nOutreach types used:")
        for outreach_type, count in outreach_counts.items():
            print(f"  - {outreach_type}: {count} activities")
    
    # Recent activities
    print(f"\nRecent activities (last 5):")
    recent_activities = filtered_df.tail(5)
    for _, row in recent_activities.iterrows():
        date = row.get('Date', 'N/A')
        specialty = row.get('MN Specialty Group', 'N/A')
        physician = row.get('FullName', 'N/A')
        print(f"  - {date}: {specialty} - {physician}")
    
    return filtered_df

def prepare_data_for_llm(df, assigned_user, max_records=10):
    """
    Prepare data in a format suitable for LLM analysis
    """
    filtered_df = filter_by_assigned_user(df, assigned_user)
    if filtered_df is None or len(filtered_df) == 0:
        return None
    
    # Get recent activities
    recent_df = filtered_df.tail(max_records)
    
    # Format for LLM
    llm_data = {
        "assigned_user": assigned_user,
        "total_activities": len(filtered_df),
        "recent_activities": []
    }
    
    for _, row in recent_df.iterrows():
        activity = {
            "date": row.get('Date', 'N/A'),
            "specialty_group": row.get('MN Specialty Group', 'N/A'),
            "physician_name": row.get('FullName', 'N/A'),
            "outreach_type": row.get('Outreach Type', 'N/A'),
            "subject": row.get('Subject', 'N/A'),
            "comments": row.get('Full Comments', 'N/A')[:200] + "..." if len(str(row.get('Full Comments', ''))) > 200 else row.get('Full Comments', 'N/A')
        }
        llm_data["recent_activities"].append(activity)
    
    return llm_data

if __name__ == "__main__":
    # Install chardet if not available
    try:
        import chardet
    except ImportError:
        print("Installing chardet for encoding detection...")
        os.system("pip install chardet")
        import chardet
    
    # Process the file
    file_path = "report1749182913520.xls"
    df, headers, assigned_counts = process_html_excel_file(file_path)
    
    if df is not None:
        # Example: Analyze for a specific user
        if assigned_counts is not None and len(assigned_counts) > 0:
            # Let's analyze the first user as an example
            first_user = assigned_counts.index[0]
            analyze_specialty_targeting(df, first_user)
            
            # Prepare data for LLM
            llm_data = prepare_data_for_llm(df, first_user)
            if llm_data:
                print(f"\n=== DATA PREPARED FOR LLM ANALYSIS ===")
                print(f"User: {llm_data['assigned_user']}")
                print(f"Total Activities: {llm_data['total_activities']}")
                print(f"Recent Activities: {len(llm_data['recent_activities'])}")
            
            # Show available users for selection
            print(f"\n\nAVAILABLE USERS FOR ANALYSIS:")
            for i, user in enumerate(assigned_counts.index):
                print(f"{i+1}. {user} ({assigned_counts[user]} activities)") 