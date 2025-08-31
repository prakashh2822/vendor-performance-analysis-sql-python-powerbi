import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
from sqlalchemy import create_engine
import logging

os.makedirs("logs", exist_ok=True)
# Configure logging
logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s-%(levelname)s-%(message)s",
    filemode="a"
)

# Create SQLite engine
engine = create_engine('sqlite:///inventory.db')

# Function to ingest CSV in chunks
def ingest_db(data, table_name, conn, if_exists="replace", chunksize=50000):
    """
    Ingest either a pandas DataFrame or a CSV file into SQLite database.
    """
    if isinstance(data, pd.DataFrame):
        # Directly insert DataFrame
        data.to_sql(table_name, con=conn, if_exists=if_exists, index=False, chunksize=chunksize)
    elif isinstance(data, str):
        # Assume it's a CSV path
        for i, chunk in enumerate(pd.read_csv(data, chunksize=chunksize)):
            if_exists_mode = "replace" if i == 0 else "append"
            chunk.to_sql(table_name, con=conn, if_exists=if_exists_mode, index=False)
    else:
        raise TypeError("ingest_db only accepts a DataFrame or CSV file path")

# Function to load all CSV files from folder
def load_raw_data():
    """
    This function will load CSV files into SQLite in chunks
    to avoid memory overload and ingest into db.
    """
    start = time.time()
    data_dir = r"C:\Users\user\practice projects\project 3\data"
    
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            file_path = os.path.join(data_dir, file)
            table_name = os.path.splitext(file)[0]  # filename without .csv
            
            logging.info(f"Processing file: {file} -> Table: {table_name}")
            
            try:
                ingest_db(file_path, table_name, engine)
                end = time.time()
                totaltime = (end - start) / 60
                logging.info(f"Successfully ingested {file} into table {table_name} "
                             f"(elapsed time: {totaltime:.2f} minutes)")
            except Exception as e:
                logging.error(f"Failed to ingest {file} into {table_name}: {e}")


# Main entry point
if __name__ == '__main__':
    load_raw_data()
