from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from datetime import datetime

import model

app = FastAPI(
    title="Prophet Forecasting API",
    description="API for time series forecasting using Prophet.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Directory to save temporary CSV files and generated plots
TEMP_DIR = "temp_data"
PLOTS_DIR = "static/plots"

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# Mount a static directory to serve generated plots
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Prophet Forecasting API is running", "status": "healthy"}


@app.post("/predict_and_plot/")
async def predict_and_plot(
    file: UploadFile = File(...),
    date_format: str = Form(..., description="Date format: 'day' or 'month'"),
    scope: int = Form(..., description="Scope for prediction: 1, 2, or 3")
):
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

    # Clean up temporary file
    if os.path.exists(temp_csv_path):
        os.remove(temp_csv_path)

    if forecast_df is None:
        raise HTTPException(status_code=500, detail="Model training or prediction failed. Check server logs for details.")

    plot_filename = f"forecast_plot_{file_id}.png"
    plot_output_path = os.path.join(PLOTS_DIR, plot_filename)

    model.show_plot(
        forecast=forecast_df,
        actual_data_df=original_df,
        title=f"Usage Prediction ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        output_path=plot_output_path
    )

    forecast_data = forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    forecast_data['ds'] = forecast_data['ds'].dt.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime to string
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
