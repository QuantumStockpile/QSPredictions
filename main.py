# import model
# import os

# if __name__ == "__main__":
#     file_to_use, action = model.create_csv()
#     if not file_to_use:
#         print("No valid filename obtained. Exiting.")
#         exit()
#     should_input_data = True
#     if os.path.exists(file_to_use):
#         print(f"File '{file_to_use}' exists.")
#         pass
#     if model.input_csv(file_to_use, action):
#         print(f"Data input for '{file_to_use}' complete.")
#     else:
#         print(f"Failed to input data for '{file_to_use}'.")
#     date_format = input("Enter date format ('day' or 'month'): ").strip().lower()
#     scope = 0
#     try:
#         scope = int(input("Enter scope (1, 2, or 3): ").strip())
#     except ValueError:
#         print("Invalid scope. Must be a number (1, 2, or 3).")
#         exit()
#     if date_format not in ['day', 'month'] or scope not in [1, 2, 3]:
#         print("Invalid date format or scope.")
#         exit()
#     forecast_result, original_df_for_plot = model.train(file=file_to_use, date_format=date_format, scope=scope)
#     if forecast_result is not None:
#         print(forecast_result[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
#         model.show_plot(forecast=forecast_result, actual_data_df=original_df_for_plot, title="Title")
#     else:
#         print("Model training or prediction failed.")
# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import uuid
from datetime import datetime

# Import your model functions
import model

app = FastAPI(
    title="Prophet Forecasting API",
    description="API for time series forecasting using Prophet.",
    version="1.0.0",
)

# Configure CORS to allow requests from your React frontend
# In a production environment, replace "*" with your frontend's specific origin (e.g., "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# Directory to save temporary CSV files and generated plots
TEMP_DIR = "temp_data"
PLOTS_DIR = "static/plots"

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# Mount a static directory to serve generated plots
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/predict_and_plot/")
async def predict_and_plot(
    file: UploadFile = File(...),
    date_format: str = Form(..., description="Date format: 'day' or 'month'"),
    scope: int = Form(..., description="Scope for prediction: 1, 2, or 3")
):
    """
    Receives a CSV file, trains a Prophet model, generates a forecast,
    and saves the plot. Returns forecast data and the plot URL.

    Args:
        file (UploadFile): The CSV file containing 'Date' and 'Value' columns.
        date_format (str): 'day' or 'month'.
        scope (int): 1, 2, or 3.

    Returns:
        JSONResponse: Contains forecast data and the URL to the generated plot.
    """
    if date_format not in ['day', 'month']:
        raise HTTPException(status_code=400, detail="Invalid date_format. Must be 'day' or 'month'.")
    if scope not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Invalid scope. Must be 1, 2, or 3.")

    # Save the uploaded file temporarily
    file_id = uuid.uuid4()
    temp_csv_path = os.path.join(TEMP_DIR, f"{file_id}.csv")
    try:
        with open(temp_csv_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")

    forecast_df, original_df = model.train(file_path=temp_csv_path, date_format=date_format, scope=scope)

    # Clean up the temporary CSV file
    os.remove(temp_csv_path)

    if forecast_df is None:
        raise HTTPException(status_code=500, detail="Model training or prediction failed. Check server logs for details.")

    # Generate a unique filename for the plot
    plot_filename = f"forecast_plot_{file_id}.png"
    plot_output_path = os.path.join(PLOTS_DIR, plot_filename)

    # Generate and save the plot
    model.show_plot(
        forecast=forecast_df,
        actual_data_df=original_df,
        title=f"Usage Prediction ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        output_path=plot_output_path
    )

    # Convert forecast DataFrame to a list of dictionaries for JSON response
    # Ensure 'ds' column is converted to string for JSON serialization
    forecast_data = forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d %H:%M:%S') # Format datetime to string
    forecast_list = forecast_data.to_dict(orient='records')

    # Construct the URL for the plot
    plot_url = f"/static/plots/{plot_filename}"

    return JSONResponse(content={
        "message": "Forecast generated successfully",
        "forecast_data": forecast_list,
        "plot_url": plot_url
    })

@app.get("/get_plot/{plot_filename}")
async def get_plot(plot_filename: str):
    """
    Serves a specific generated plot image.

    Args:
        plot_filename (str): The filename of the plot to retrieve.

    Returns:
        FileResponse: The image file.
    """
    file_path = os.path.join(PLOTS_DIR, plot_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Plot not found.")
    return FileResponse(file_path, media_type="image/png")

# You can add more endpoints if needed, e.g., to just get raw forecast data
# without generating a plot, or to handle different input types.
