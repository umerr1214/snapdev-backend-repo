from fastapi import APIRouter, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import gspread
from datetime import datetime

load_dotenv()

router = APIRouter()

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Google Sheet ID and range from environment variables
SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', 'YOUR_SPREADSHEET_ID')  # Add a default or ensure it's in .env
RANGE_NAME = os.getenv('GOOGLE_SHEET_RANGE', 'Sheet1!A1:B') # Add a default or ensure it's in .env


def get_sheet_data():
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Sheet1')

    if not spreadsheet_id:
        raise ValueError("GOOGLE_SPREADSHEET_ID environment variable not set.")

    creds_json = {
        "type": os.getenv("GOOGLE_SERVICE_ACCOUNT_TYPE"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
        "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
    }
    
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)
    return worksheet.get_all_records(), spreadsheet_id

@router.get("/sheet-data")
async def read_sheet_data():
    """API endpoint to get and process sheet data."""
    try:
        all_rows, spreadsheet_id = get_sheet_data()
        if not all_rows:
            return {"message": "No data found."}

        # Calculate total hours using the same logic as client-hours endpoint
        try:
            import pandas as pd
            from datetime import timedelta
            
            df = pd.DataFrame(all_rows)
            
            # Check if required columns exist (case-insensitive)
            required_columns = ["Client Name", "Start Time (PKT)", "End Time (PKT)", "Engineer Name", "Date"]
            
            # Map columns to standard names
            column_mapping = {}
            for req_col in required_columns:
                for df_col in df.columns:
                    if req_col.lower().strip() == df_col.lower().strip():
                        column_mapping[df_col] = req_col
                        break
            
            # Rename columns to standard names
            df = df.rename(columns=column_mapping)
            
            # Check if all required columns are present after mapping
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"⚠️ Missing required columns for total calculation: {missing_columns}")
                total_hours = 0
            else:
                # Calculate total minutes using the same logic
                def calculate_minutes(row):
                    try:
                        start_time_str = str(row["Start Time (PKT)"]).strip()
                        end_time_str = str(row["End Time (PKT)"]).strip()
                        
                        time_formats = ["%I:%M:%S %p", "%H:%M:%S", "%I:%M %p", "%H:%M"]
                        
                        start_time = None
                        end_time = None
                        
                        for fmt in time_formats:
                            try:
                                start_time = datetime.strptime(start_time_str, fmt)
                                end_time = datetime.strptime(end_time_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if start_time is None or end_time is None:
                            return 0
                        
                        if end_time < start_time:
                            end_time += timedelta(days=1)
                        
                        return int((end_time - start_time).seconds / 60)
                    except Exception:
                        return 0

                df["Minutes"] = df.apply(calculate_minutes, axis=1)
                total_minutes = df["Minutes"].sum()
                total_hours = total_minutes / 60  # Convert to hours
                
        except Exception as e:
            print(f"Error calculating total hours: {e}")
            total_hours = 0

        return {
            "sheet_id": spreadsheet_id,
            "total_hours": round(total_hours, 2),
            "raw_data": all_rows
        }
    except gspread.exceptions.SpreadsheetNotFound:
        raise HTTPException(status_code=404, detail="Spreadsheet not found. Please check the spreadsheet ID and permissions.")
    except gspread.exceptions.WorksheetNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing sheet data: {e}")

@router.get("/client-hours")
async def get_client_hours_from_sheet():
    """API endpoint to get and calculate client hours from sheet data using the same logic as CSV upload."""
    try:
        all_rows, _ = get_sheet_data()
        
        # Convert sheet data to DataFrame-like structure for consistent processing
        import pandas as pd
        from datetime import timedelta
        
        if not all_rows:
            return []
        
        # Create a DataFrame from the sheet data
        df = pd.DataFrame(all_rows)
        
        # Debug: Print column names to see what we're working with
        print(f"📊 Sheet columns: {list(df.columns)}")
        print(f"📏 Sheet shape: {df.shape}")
        
        # Check if required columns exist (case-insensitive)
        required_columns = ["Client Name", "Start Time (PKT)", "End Time (PKT)", "Engineer Name", "Date"]
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        # Map columns to standard names
        column_mapping = {}
        for req_col in required_columns:
            for df_col in df.columns:
                if req_col.lower().strip() == df_col.lower().strip():
                    column_mapping[df_col] = req_col
                    break
        
        print(f"🔗 Column mapping: {column_mapping}")
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Check if all required columns are present after mapping
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠️ Missing required columns: {missing_columns}. Available columns: {list(df.columns)}")
            return []

        # Normalize client names (case-insensitive)
        df["Client Name"] = df["Client Name"].str.strip().str.title()

        # Step 3: Parse times & calculate duration in minutes (same logic as CSV upload)
        def calculate_minutes(row):
            try:
                start_time_str = str(row["Start Time (PKT)"]).strip()
                end_time_str = str(row["End Time (PKT)"]).strip()
                
                print(f"🕐 Parsing times: '{start_time_str}' to '{end_time_str}'")
                
                # Try different time formats
                time_formats = ["%I:%M:%S %p", "%H:%M:%S", "%I:%M %p", "%H:%M"]
                
                start_time = None
                end_time = None
                
                for fmt in time_formats:
                    try:
                        start_time = datetime.strptime(start_time_str, fmt)
                        end_time = datetime.strptime(end_time_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if start_time is None or end_time is None:
                    print(f"❌ Could not parse time format for: '{start_time_str}' to '{end_time_str}'")
                    return 0
                
                # Handle overnight shift
                if end_time < start_time:
                    end_time += timedelta(days=1)
                
                minutes = int((end_time - start_time).seconds / 60)
                print(f"⏱️ Calculated {minutes} minutes")
                return minutes
            except Exception as e:
                print(f"❌ Time parsing error: {e} for row: {row.to_dict()}")
                return 0

        df["Minutes"] = df.apply(calculate_minutes, axis=1)

        # Step 4: Convert minutes → HH:MM
        def minutes_to_hhmm(minutes):
            hours, mins = divmod(minutes, 60)
            return f"{hours:02}:{mins:02}"

        # Step 5: Build breakdown (Engineer + HH:MM + Date)
        df["Breakdown"] = (
            df["Engineer Name"].str.strip() +
            " (" + df["Minutes"].apply(minutes_to_hhmm) + ")" +
            " on " + df["Date"].astype(str)
        )

        # Step 6: Group by client
        summary = df.groupby("Client Name").agg({
            "Minutes": "sum",
            "Breakdown": lambda x: " || ".join(x)
        }).reset_index()

        # Step 7: Sort descending by total minutes (before converting to string)
        summary = summary.sort_values(by="Minutes", ascending=False)

        # Step 8: Convert total minutes → HH:MM
        summary["Total Hours Used"] = summary["Minutes"].apply(minutes_to_hhmm)
        summary = summary.drop(columns=["Minutes"])

        # Step 9: Reorder columns
        summary = summary[["Client Name", "Total Hours Used", "Breakdown"]]

        return summary.to_dict(orient="records")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Sheet processing error: {e}")
        print(f"📋 Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")