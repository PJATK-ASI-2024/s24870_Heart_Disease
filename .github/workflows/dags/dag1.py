from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
import gspread
from google.oauth2.service_account import Credentials

# Funkcja do pobierania danych
def download_data():
    try:
        df = pd.read_csv("/opt/airflow/dags/heart_disease_cleaned.csv")
        df.to_csv("/opt/airflow/dags/data.csv", index=False)
        print("Plik został pobrany i zapisany jako 'data.csv'")
    except Exception as e:
        raise Exception(f"Błąd podczas pobierania danych: {e}")

# Funkcja do podziału danych
def split_data():
    try:
        df = pd.read_csv("/opt/airflow/dags/data.csv")
        train, test = train_test_split(df, test_size=0.3, random_state=42)
        train.to_csv("/opt/airflow/dags/modelowy.csv", index=False)
        test.to_csv("/opt/airflow/dags/douczeniowy.csv", index=False)
        print("Dane podzielone na 'modelowy.csv' i 'douczeniowy.csv'")
    except Exception as e:
        raise Exception(f"Błąd podczas podziału danych: {e}")

# Funkcja do zapisywania danych w Google Sheets
def upload_to_google_sheets():
    try:
        # Autoryzacja Google Sheets
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            "/opt/airflow/dags/credentials.json", scopes=scopes
        )
        client = gspread.authorize(credentials)

        # Tworzenie nowego arkusza Google Sheets
        folder_id = "17NDgPfAXHWNjiU32zH-84SRePHb73ujh"
        sheet_title = "Zbiór modelowy"
        spreadsheet = client.create(sheet_title, folder_id=folder_id)
        sheet_title_2 = "Zbiór douczeniowy"
        spreadsheet2 = client.create(sheet_title_2, folder_id=folder_id)

        # Pobierz dane z plików CSV
        train_data = pd.read_csv("/opt/airflow/dags/modelowy.csv")
        test_data = pd.read_csv("/opt/airflow/dags/douczeniowy.csv")

        # Dodaj dane treningowe
        worksheet = spreadsheet.sheet1
        worksheet.update([train_data.columns.values.tolist()] + train_data.values.tolist())

        # Dodaj dane testowe
        worksheet2 = spreadsheet2.sheet1
        worksheet2.update([test_data.columns.values.tolist()] + test_data.values.tolist())

        print("Dane zostały zapisane w Google Sheets")
    except Exception as e:
        raise Exception(f"Błąd podczas zapisywania danych w Google Sheets: {e}")

# Konfiguracja DAG-a
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 20),
    "retries": 1,
}

with DAG(
    "process_heart_disease_data",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    task_download = PythonOperator(
        task_id="download_data",
        python_callable=download_data
    )

    task_split = PythonOperator(
        task_id="split_data",
        python_callable=split_data
    )

    task_upload = PythonOperator(
        task_id="upload_to_google_sheets",
        python_callable=upload_to_google_sheets
    )

    task_download >> task_split >> task_upload



