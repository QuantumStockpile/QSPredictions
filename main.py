import model
import os

if __name__ == "__main__":
    file_to_use, action = model.create_csv()
    if not file_to_use:
        print("No valid filename obtained. Exiting.")
        exit()
    should_input_data = True
    if os.path.exists(file_to_use):
        print(f"File '{file_to_use}' exists.")
        pass
    if model.input_csv(file_to_use, action):
        print(f"Data input for '{file_to_use}' complete.")
    else:
        print(f"Failed to input data for '{file_to_use}'.")
    date_format = input("Enter date format ('day' or 'month'): ").strip().lower()
    scope = 0
    try:
        scope = int(input("Enter scope (1, 2, or 3): ").strip())
    except ValueError:
        print("Invalid scope. Must be a number (1, 2, or 3).")
        exit()
    if date_format not in ['day', 'month'] or scope not in [1, 2, 3]:
        print("Invalid date format or scope.")
        exit()
    forecast_result, original_df_for_plot = model.train(file=file_to_use, date_format=date_format, scope=scope)
    if forecast_result is not None:
        print(forecast_result[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
        model.show_plot(forecast=forecast_result, actual_data_df=original_df_for_plot, title="Title")
    else:
        print("Model training or prediction failed.")
