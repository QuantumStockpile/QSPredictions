import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt


def train(file_path: str, date_format: str, scope: int):
    """
    Train a Prophet model and generate forecasts
    
    Args:
        file_path: Path to CSV file with 'Date' and 'Value' columns
        date_format: 'day' or 'month' for forecast frequency
        scope: 1, 2, or 3 for forecast duration (years for daily, years*12 for monthly)
    
    Returns:
        tuple: (forecast_dataframe, actual_data_dataframe) or (None, None) on error
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {file_path}")
        return None, None
    except Exception as e:
        print(f"Error reading CSV file '{file_path}': {e}")
        return None, None

    try:
        df = df.rename(columns={'Date': 'ds', 'Value': 'y'})
    except KeyError as e:
        print(f"Error: Missing expected column for Prophet. Ensure you have 'Date' and 'Value' headers. Missing: {e}")
        return None, None

    try:
        df['ds'] = pd.to_datetime(df['ds'])
    except Exception as e:
        print(f"Error converting 'Date' column to datetime: {e}")
        return None, None

    try:
        df['y'] = pd.to_numeric(df['y'])
    except Exception as e:
        print(f"Error converting 'Value' column to numeric: {e}")
        return None, None

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

    if future.empty:
        print("Generated future dataframe is empty. Cannot predict.")
        return None, None

    forecast = m.predict(future)
    return forecast, df


def show_plot(forecast, actual_data_df, title="Prophet Forecast", output_path="forecast_plot.png"):
    """
    Generate and save a forecast plot
    
    Args:
        forecast: Prophet forecast dataframe
        actual_data_df: Original data dataframe
        title: Plot title
        output_path: Path to save the plot image
    """
    plt.figure(figsize=(12, 6))
    plt.plot(actual_data_df['ds'], actual_data_df['y'], 'k.', label='Actual Data')
    plt.plot(forecast['ds'], forecast['yhat'], color='blue', label='Forecast')
    plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], 
                     color='skyblue', alpha=0.4, label='Confidence Interval')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    try:
        plt.savefig(output_path)
        print(f"Plot saved to {output_path}")
    except Exception as e:
        print(f"Error saving plot to {output_path}: {e}")
    finally:
        plt.close()
