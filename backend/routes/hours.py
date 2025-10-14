from fastapi import APIRouter, File, UploadFile, HTTPException
import pandas as pd
from datetime import datetime, timedelta
import io

router = APIRouter()

# In-memory storage for the processed data
client_hours_data = None

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    global client_hours_data
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        contents = await file.read()
        if not contents:
            raise ValueError("The uploaded file is empty")
        
        try:
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        except UnicodeDecodeError:
            raise ValueError("The uploaded file is not a valid CSV file or contains invalid characters")
        except pd.errors.EmptyDataError:
            raise ValueError("The uploaded CSV file is empty")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error parsing CSV file: {str(e)}")
        
        # Debug: Print column names to see what we're working with
        print(f"📊 CSV columns: {list(df.columns)}")
        print(f"📏 CSV shape: {df.shape}")
        
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
            raise ValueError(f"Missing required columns: {missing_columns}. Available columns: {list(df.columns)}")

        # Normalize client names (case-insensitive)
        df["Client Name"] = df["Client Name"].str.strip().str.title()

        # Step 3: Parse times & calculate duration in minutes
        def calculate_minutes(row):
            try:
                start_time_str = str(row["Start Time (PKT)"]).strip()
                end_time_str = str(row["End Time (PKT)"]).strip()
                
                print(f"🕐 Parsing times: '{start_time_str}' to '{end_time_str}'")
                
                start = datetime.strptime(start_time_str, "%I:%M:%S %p")
                end = datetime.strptime(end_time_str, "%I:%M:%S %p")
                # Handle overnight shift
                if end < start:
                    end += timedelta(days=1)
                minutes = int((end - start).seconds / 60)
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

        client_hours_data = summary.to_dict(orient="records")

        return {"message": "File uploaded and processed successfully."}

    except ValueError as e:
        # Validation errors should return 422
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Upload error: {e}")
        print(f"📋 Traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/hours")
async def get_client_hours():
    if client_hours_data is None:
        return []
    return client_hours_data