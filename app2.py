from flask import Flask, jsonify, render_template, request
import datetime
import time
import json
import csv
import socket
import threading
import os

DATA_DIR = 'lastwork'
CSV_FILENAME = 'sensor_data.csv'
DEFAULT_FILENAME = DATA_DIR + '/' + CSV_FILENAME

# Socket通信用の設定（grp07_server.py から引き継ぎ）
SOCKET_HOST = '0.0.0.0'  # すべてのインターフェースからの接続を許可
SOCKET_PORT = 8765       # Raspberry Piからの送信先ポート

app = Flask(__name__)

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# CSVにデータを書き込む共通関数
def csv_write_iterator(data_list, filename0=DEFAULT_FILENAME):
    with open(filename0, mode='a', encoding='utf-8', newline='') as f:
        write_iter = csv.writer(f)
        write_iter.writerow(data_list)

# 【A】Raspberry PiからのSocket通信を待ち受けるバックグラウンド関数
def socket_server_loop():
    # TCPソケットの作成
    socket_w = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_w.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_w.bind((SOCKET_HOST, SOCKET_PORT))
    socket_w.listen(5)
    
    print(f"[*] Socket Server started. Waiting for Raspberry Pi on port {SOCKET_PORT}...")
    
    while True:
        try:
            socket_s_r, client_address = socket_w.accept()
            print(f"[Socket] Connection from {client_address}")

            # データ受信 (最大1024バイト)
            data_r = socket_s_r.recv(1024)
            if not data_r:
                socket_s_r.close()
                continue
                
            data_r_str = data_r.decode('utf-8')
            print(f"[Socket] Received raw string: {data_r_str}")

            # JSON文字列を辞書型に変換
            data_dict = json.loads(data_r_str)

            # データの抽出とCSV保存
            ts = data_dict.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            tp = data_dict.get("temperature", "-")
            hm = data_dict.get("humidity", "-")
            co2 = data_dict.get("co2", "-")
            nm = data_dict.get("name", "-")
             # Raspberry Pi側から送られてくる想定

            # HTML/JS側の想定に合わせた並び順 [時刻, 温度, 湿度, 学籍番号, CO2]
            row = [ts, tp, hm,co2, nm ]

            csv_write_iterator(row)
            print(f"[Socket] Successfully saved to CSV: {row}")

            socket_s_r.close()

        except Exception as e:
            print(f"[Socket Error] {e}")
            time.sleep(1)

# 【B】AndroidやブラウザからのHTTPリクエストを処理するルーティング
@app.route("/", methods=["GET"])
def index1():
    data_list = []
    if os.path.exists(DEFAULT_FILENAME):
        with open(DEFAULT_FILENAME, mode='r', encoding='utf-8') as f:
            for line in f:
                line = line.replace('\n', '')
                if line:
                    data_list.append(line.split(','))
    return render_template("HTML_iteration_g7.html", input_from_python=data_list)

@app.route("/submit", methods=["POST"])
def submit():
    try:

        print(f"[Debug] request.formの中身: {request.form}")
        
        tp = request.form.get('temperature', '-')
        hm = request.form.get('humidity', '-')
        co2 = request.form.get('co2', '-')
        nm = request.form.get('student_id', '-')

        ts = datetime.datetime.now().strftime("%Y-%m-%d H:%M:%S")

        row = [ts, tp, hm, co2, nm]

        csv_write_iterator(row)
        print(f"[HTTP Submit] Successfully saved to CSV: {row}")

        return "Success", 200
    except Exception as e:
        print(f"[HTT` Submit Error] {e}")
        return "Internal Server Error", 500

# Androidアプリが最新の1件を取得するためのHTTP API
# Androidアプリが最新の1件を取得するためのHTTP API
# latest の中身
@app.route("/latest", methods=["GET"])
def latest():
    if os.path.exists(DEFAULT_FILENAME):
        with open(DEFAULT_FILENAME, mode='r', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if rows:
                latest_row = rows[-1]
                if len(latest_row) >= 5:
                    # すでに CSV が [時刻, 温度, 湿度, CO2, 学籍番号] の順なのでそのまま返す
                    csv_response = ",".join(latest_row[:5])
                    return csv_response, 200, {'Content-Type': 'text/plain'}
    return "No data available", 404
    
if __name__ == "__main__":
    # 1. Socket通信サーバーを別スレッドで起動
    socket_thread = threading.Thread(target=socket_server_loop, daemon=True)
    socket_thread.start()
    
    # 2. Flask（HTTPサーバー）をメインスレッドで起動
    # Androidからアクセスできるように host="0.0.0.0" に設定
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False  # スレッドをマルチに動かすため、debug=Falseを推奨
    )