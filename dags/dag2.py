from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Ścieżka do pliku z poświadczeniami
SERVICE_ACCOUNT_FILE = '/opt/airflow/dags/credentials.json'

# Funkcja do pobrania danych z Google Sheets
def fetch_data_from_google_sheets():
    # Ustawienie poświadczeń
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(credentials)

    # Pobierz dane z arkusza "Zbiór modelowy"
    model_sheet = client.open("Zbiór modelowy").sheet1
    model_data = model_sheet.get_all_records()
    model_df = pd.DataFrame(model_data)
    model_df.to_csv('/tmp/nowy_modelowy.csv', index=False)  # Zapisz do pliku CSV

    # Pobierz dane z arkusza "Zbiór douczeniowy"
    learning_sheet = client.open("Zbiór douczeniowy").sheet1
    learning_data = learning_sheet.get_all_records()
    learning_df = pd.DataFrame(learning_data)
    learning_df.to_csv('/tmp/nowy_douczeniowy.csv', index=False)  # Zapisz do pliku CSV

# Funkcja do czyszczenia danych
def clean_data():
    # Wczytaj dane z obu plików
    model_df = pd.read_csv('/tmp/nowy_modelowy.csv')
    learning_df = pd.read_csv('/tmp/nowy_douczeniowy.csv')

    # Czyszczenie danych
    model_df.dropna(inplace=True)
    model_df.drop_duplicates(inplace=True)
    learning_df.dropna(inplace=True)
    learning_df.drop_duplicates(inplace=True)

    # Zapisz oczyszczone dane
    model_df.to_csv('/tmp/nowe_cleaned_modelowy.csv', index=False)
    learning_df.to_csv('/tmp/nowe_cleaned_douczeniowy.csv', index=False)

# Funkcja do standaryzacji i normalizacji danych
def standardize_and_normalize_data():
    # Wczytaj oczyszczone dane
    model_df = pd.read_csv('/tmp/nowe_cleaned_modelowy.csv')
    learning_df = pd.read_csv('/tmp/nowe_cleaned_douczeniowy.csv')

    # Standaryzacja i normalizacja dla "Zbiór modelowy"
    scaler = StandardScaler()
    normalizer = MinMaxScaler()
    numeric_columns_model = model_df.select_dtypes(include=['float64', 'int64']).columns
    model_df[numeric_columns_model] = normalizer.fit_transform(
        scaler.fit_transform(model_df[numeric_columns_model])
    )

    # Standaryzacja i normalizacja dla "Zbiór douczeniowy"
    numeric_columns_learning = learning_df.select_dtypes(include=['float64', 'int64']).columns
    learning_df[numeric_columns_learning] = normalizer.fit_transform(
        scaler.fit_transform(learning_df[numeric_columns_learning])
    )

    # Zapisz przetworzone dane
    model_df.to_csv('/tmp/nowe_processed_modelowy.csv', index=False)
    learning_df.to_csv('/tmp/nowe_processed_douczeniowy.csv', index=False)

# Funkcja do przesłania danych do Google Sheets z nowymi nazwami arkuszy
def upload_data_to_google_sheets():
    # Wczytaj przetworzone dane
    model_df = pd.read_csv('/tmp/nowe_processed_modelowy.csv')
    learning_df = pd.read_csv('/tmp/nowe_processed_douczeniowy.csv')

    # Połącz się z Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(credentials)

    folder_id = "17NDgPfAXHWNjiU32zH-84SRePHb73ujh"
    sheet_title = "Zbiór modelowy wyczyszczony"
    spreadsheet = client.create(sheet_title, folder_id=folder_id)
    sheet_title_2 = "Zbiór douczeniowy wyczyszczony"
    spreadsheet2 = client.create(sheet_title_2, folder_id=folder_id)

    # Utwórz nowy arkusz dla przetworzonych danych modelowych
    worksheet = spreadsheet.sheet1
    worksheet.update([model_df.columns.values.tolist()] + model_df.values.tolist())

    # Utwórz nowy arkusz dla przetworzonych danych douczeniowych
    worksheet2 = spreadsheet2.sheet1
    worksheet2.update([learning_df.columns.values.tolist()] + learning_df.values.tolist())


# Tworzenie DAG-a
default_args = {
    'start_date': datetime(2023, 11, 1),
}

with DAG('data_processing_dag', default_args=default_args, schedule_interval=None) as dag:
    fetch_data_task = PythonOperator(
        task_id='fetch_data_from_google_sheets',
        python_callable=fetch_data_from_google_sheets,
    )

    clean_data_task = PythonOperator(
        task_id='clean_data',
        python_callable=clean_data,
    )

    normalize_data_task = PythonOperator(
        task_id='normalize_data',
        python_callable=standardize_and_normalize_data,
    )

    upload_data_task = PythonOperator(
        task_id='upload_data_to_google_sheets',
        python_callable=upload_data_to_google_sheets,
    )

    # Kolejność zadań
    fetch_data_task >> clean_data_task >> normalize_data_task >> upload_data_task

