import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsTool:
    def __init__(self, spreadsheet_name="HVAC Outreach Campaign", worksheet_name="Leads"):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        self.credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "intense-hour-427605-v6-4f484685ddf0.json")
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, self.scope
        )
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open(spreadsheet_name)
        self.worksheet = self.spreadsheet.worksheet(worksheet_name)

    def get_next_task(self, status_to_find: str):
        """Finds the next row with a given status and returns it as a dictionary."""
        try:
            records = self.worksheet.get_all_records()
            for i, row in enumerate(records):
                if row.get("Status") == status_to_find:
                    row['row_index'] = i + 2  # +2 to account for header and 0-indexing
                    return row
            return None
        except Exception as e:
            print(f"An error occurred while getting the next task: {e}")
            return None

    def update_row(self, row_index: int, update_data: dict):
        """Updates a specific row by its index with new data."""
        try:
            header = self.worksheet.row_values(1)
            for col_name, new_value in update_data.items():
                try:
                    if col_name in header:
                        col_index = header.index(col_name) + 1
                        self.worksheet.update_cell(row_index, col_index, new_value)
                    else:
                        print(f"Warning: Column '{col_name}' not found in sheet.")
                except Exception as e:
                    print(f"An error occurred updating cell {row_index, col_name}: {e}")
            return f"Successfully updated row {row_index}."
        except Exception as e:
            print(f"An error occurred while updating the row: {e}")
            return None

    def append_rows(self, data_df: pd.DataFrame):
        """Appends new rows from a DataFrame to the worksheet, aligning columns."""
        try:
            header = self.worksheet.row_values(1)

            if not header:
                # If the sheet is empty, write the header and all the data
                values_to_append = [data_df.columns.tolist()] + data_df.values.tolist()
            else:
                # If the sheet has a header, align the DataFrame to it
                # Create a mapping from lower-case, stripped header to original header
                header_map = {h.strip().lower(): h for h in header}
                
                # Normalize df columns for matching
                df_columns_map = {c.strip().lower(): c for c in data_df.columns}

                values_to_append = []
                for _, row in data_df.iterrows():
                    row_to_append = []
                    for h_lower, h_original in header_map.items():
                        if h_lower in df_columns_map:
                            original_df_col = df_columns_map[h_lower]
                            row_to_append.append(row[original_df_col])
                        else:
                            row_to_append.append('')  # Add empty string for missing columns
                    values_to_append.append(row_to_append)

            if values_to_append:
                self.worksheet.append_rows(values_to_append, value_input_option='USER_ENTERED')
                return f"Successfully appended {len(data_df)} rows."
            else:
                return "No data to append."

        except Exception as e:
            print(f"An error occurred while appending rows: {e}")
            return None

    def clear_sheet(self):
        """Clears all data and formatting from the worksheet."""
        try:
            self.worksheet.clear()
            return "Worksheet cleared successfully."
        except Exception as e:
            print(f"An error occurred while clearing the sheet: {e}")
            return None

    def ensure_columns_exist(self, required_columns: list):
        """Checks if required columns exist in the header and adds them if they don't."""
        try:
            header = []
            try:
                header = self.worksheet.row_values(1)
            except gspread.exceptions.APIError as e:
                # This can happen if the sheet is completely empty
                if 'exceeds grid limits' in str(e):
                     pass 
                else:
                    raise e
            
            existing_columns = set(header)
            missing_columns = [col for col in required_columns if col not in existing_columns]

            if missing_columns:
                print(f"Adding missing columns to the sheet: {missing_columns}")
                
                start_col_index = len(header) + 1
                cell_list = []
                for i, col_name in enumerate(missing_columns):
                    cell_list.append(gspread.Cell(1, start_col_index + i, value=col_name))
                
                if cell_list:
                    self.worksheet.update_cells(cell_list)

            return "Column check complete."
        except Exception as e:
            print(f"An error occurred while ensuring columns exist: {e}")
            return None