import pandas as pd

def export_tuple_to_excel(data_tuple, filename):
    """
    Exports a tuple of data to an Excel spreadsheet using pandas.

    Args:
        data_tuple (tuple): The tuple containing the data to export.
        filename (str): The name of the Excel file to create.
    """
    column_names = ["user_id", "username", "password", "email", "join_date", "last_login", "is_private"]

    # Ensure the number of column names matches the length of the data tuple
    if len(column_names) != len(data_tuple):
        raise ValueError("Number of column names must match the length of the data tuple.")

    # Create a DataFrame from the data tuple
    df = pd.DataFrame([data_tuple], columns=column_names)

    # Save the DataFrame to an Excel file
    df.to_excel(filename, index=False)

# Example usage
data_tuple = (1001, "ameliaxx", "54fcf974eabb0444320acd2835977b2c686b916162e6571668ac45db549da031", "amelia34@gmail.com", "2024-05-15", "2024-08-16 22:43", 0)
filename = "data.xlsx"

export_tuple_to_excel(data_tuple, filename)

print(f"Data exported to Excel file: {filename}")
