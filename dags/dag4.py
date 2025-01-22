from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import pickle
import os

def train_model():
    os.makedirs('/models', exist_ok=True)
    os.makedirs('/reports', exist_ok=True)
    # Wczytaj dane
    df = pd.read_csv('/processed_data/processed_data.csv')
    X = df.drop('target_column', axis=1)
    y = df['target_column']

    # Podziel dane
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Trenuj model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Ewaluacja
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Zapisz model
    with open('/models/model.pkl', 'wb') as f:
        pickle.dump(model, f)

    # Zapisz raport
    with open('/reports/evaluation_report.txt', 'w') as f:
        f.write(f'Accuracy: {accuracy}')

with DAG(
    dag_id='model_training_dag',
    schedule=None,
    catchup=False,
    start_date=datetime(2025, 1, 1)
) as dag:
    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model
    )
