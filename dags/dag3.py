from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def process_data():
    os.makedirs('/processed_data', exist_ok=True)
    os.makedirs('/visualizations', exist_ok=True)
    # Pobierz dane
    df = pd.read_csv('/dags/data_data.csv')
    # Usuń duplikaty
    df.drop_duplicates(inplace=True)
    # Uzupełnij braki
    df.fillna(df.median(numeric_only=True), inplace=True)
    # Standaryzacja tylko kolumn numerycznych (bez target_column)
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if 'target_column' in numeric_cols:
        numeric_cols = numeric_cols.drop('target_column')  # Usuń 'target_column'
    df[numeric_cols] = (df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std()
    # Zapisz dane
    df.to_csv('/processed_data/processed_data.csv', index=False)

    # Wizualizacja
    sns.pairplot(df.select_dtypes(include=['float64', 'int64']))
    plt.savefig('/visualizations/pairplot.png')

with DAG(
    dag_id='data_processing_dag',
    schedule=None,
    catchup=False,
    start_date=datetime(2025, 1, 1)
) as dag:
    process_data_task = PythonOperator(
        task_id='process_data',
        python_callable=process_data
    )
