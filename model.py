import pandas as pd
from prophet import Prophet
import os
import csv
import matplotlib.pyplot as plt


# add check for leap year
def train(file, date_format, scope):
    df = pd.read_csv(file)
    try:
        df = df.rename(columns={'Date': 'ds', 'Value': 'y'})
    except KeyError as e:
        print(f"Error: Missing expected column for Prophet. Ensure you have 'Date' and 'Value' headers. Missing: {e}")
        return None, None
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = pd.to_numeric(df['y'])
    m = Prophet()
    m.fit(df)
    future = None
    if date_format == "day":
        if scope == 1:
            future = m.make_future_dataframe(periods=365)
        elif scope == 2:
            future = m.make_future_dataframe(periods=730)
        elif scope == 3:
            future = m.make_future_dataframe(periods=1095)
    elif date_format == "month":
        if scope == 1:
            future = m.make_future_dataframe(periods=12, freq='MS')
        elif scope == 2:
            future = m.make_future_dataframe(periods=24, freq='MS')
        elif scope == 3:
            future = m.make_future_dataframe(periods=36, freq='MS')

    if future is None:
        print("Invalid date format or scope provided.")
        return None, None
    forecast = m.predict(future)
    return forecast, df


def create_csv():
    while True:
        filename = input("Enter filename: ").strip().lower()
        if not filename:
            print("Filename cannot be empty. Please try again.")
            continue
        if not filename.endswith('.csv'):
            filename += '.csv'
        if os.path.exists(filename):
            print(f"File '{filename}' already exists.")
            action = input("Do you want to overwrite(o), append(a), or use(u) existing for training? ").strip().lower()
            if action == 'o':
                print(f"Overwriting '{filename}'.")
                return filename, 'overwrite'
            elif action == 'a':
                print(f"Appending to '{filename}'.")
                return filename, 'append'
            elif action == 'u':
                print(f"Using existing file '{filename}'.")
                return filename, 'use_existing'
            else:
                print("Invalid choice. Try again.")
                continue
        else:
            return filename, 'create_new'


def input_csv(filename, action):
    if action == 'use_existing':
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist, but 'use existing' was chosen.")
            return False
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader, None)
                if headers:
                    print("Headers:", ", ".join(headers))
                else:
                    print("File has no headers.")
                row_count = 0
                for i, row in enumerate(reader):
                    print(", ".join(row))
                    row_count += 1
                if row_count == 0 and not headers:
                    print("File is empty.")
            return True
        except Exception as e:
            print(f"Error reading existing file '{filename}': {e}")
            return False
    file_exists = os.path.exists(filename)
    current_headers = []
    if action == 'append' and file_exists:
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                current_headers = next(reader, [])  # Read existing headers
                if not current_headers:
                    print("Existing file is empty or has no headers. Will treat as new file for data input.")
                    file_exists = False  # Treat as new if no headers
        except Exception as e:
            print(f"Error reading existing file '{filename}': {e}")
            current_headers = []  # Reset if error
            file_exists = False  # Treat as new if error reading
    if file_exists and current_headers:
        print(f"Existing headers: {', '.join(current_headers)}")
        headers = current_headers
        print(f"Using existing headers for append: {', '.join(headers)}")
    else:
        headers_input = input("Enter column headers (comma-separated, e.g., Date,Value): ").strip()
        if not headers_input:
            print("No headers provided. Exiting CSV input.")
            return False
        headers = [h.strip() for h in headers_input.split(',')]
    num_columns = len(headers)
    data_rows = []
    row_number = 1
    while True:
        row_input = input(f"Enter data for Row {row_number} (comma-separated, or 'done' to finish): ").strip()
        if row_input.lower() == 'done':
            break
        if not row_input:
            print("Row cannot be empty.")
            continue
        values = [v.strip() for v in row_input.split(',')]
        if len(values) != num_columns:
            print(f"Error: Expected {num_columns} values but got {len(values)}.")
            print(f"Headers are: {', '.join(headers)}")
            continue
        data_rows.append(values)
        row_number += 1
    if not data_rows:
        print("No data rows entered.")
        return True
    try:
        mode = 'w'
        if action == 'append' and file_exists and headers == current_headers:
            mode = 'a'
        write_headers = False
        if mode == 'w' or (mode == 'a' and (not file_exists or not current_headers)):
            write_headers = True
        with open(filename, mode, newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            if write_headers:
                csv_writer.writerow(headers)
            csv_writer.writerows(data_rows)
        print(f"CSV file '{filename}' updated successfully with {len(data_rows)} new rows.")
        return True
    except IOError as e:
        print(f"Error writing to file '{filename}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def show_plot(forecast, actual_data_df, title="Prophet Forecast"):
    fig = plt.figure(figsize=(12, 6))
    plt.plot(actual_data_df['ds'], actual_data_df['y'], 'k.', label='Actual Data')
    plt.plot(forecast['ds'], forecast['yhat'], color='blue', label='Forecast')
    plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='skyblue', alpha=0.4, label='Confidence Interval')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
