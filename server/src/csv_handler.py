import csv
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# CI環境などで環境変数がセットされていない場合でも落ちないよう、初期値を設定
DATA_DIR = os.getenv('DATA_DIR', './lastwork')
CSV_FILENAME = os.getenv('CSV_FILENAME', 'sensor_data.csv')

DEFAULT_FILENAME = os.path.join(DATA_DIR, CSV_FILENAME)

file_lock = threading.Lock()

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_sensor_row(row, filename=DEFAULT_FILENAME):
    ensure_data_dir()

    with file_lock:
        with open(filename, mode='a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

def read_all_rows(filename=DEFAULT_FILENAME):
    data_list = []
    with file_lock:
        if os.path.exists(filename):
            with open(filename, mode='r', encoding='utf-8') as f:
                for line in f:
                    line = line.replace('\n', '').strip()
                    if line:
                        data_list.append(line.split(','))
    return data_list

def get_latest_row(filename=DEFAULT_FILENAME):
    with file_lock:
        if os.path.exists(filename):
            with open(filename, mode='r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
                if rows:
                    return rows[-1]
    return None