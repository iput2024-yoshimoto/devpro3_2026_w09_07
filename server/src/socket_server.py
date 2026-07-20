import socket
import json
import datetime
import time
import os
from dotenv import load_dotenv
from server.src.csv_handler import save_sensor_row

load_dotenv()

SOCKET_HOST = os.getenv('SOCKET_HOST')
SOCKET_PORT = int(os.getenv('SOCKET_PORT'))

def socket_server_loop():
    socket_w = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_w.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_w.bind((SOCKET_HOST, SOCKET_PORT))
    socket_w.listen(5)

    print(f"[*] Socket Server started. Waiting for Raspberry Pi on {SOCKET_HOST}:{SOCKET_PORT}...")
    
    while True:
            try:
                socket_s_r, client_address = socket_w.accept()
                print(f"[Socket] Connection from {client_address}")

                data_r = socket_s_r.recv(1024)
                if not data_r:
                    socket_s_r.close()
                    continue
                    
                data_r_str = data_r.decode('utf-8')
                print(f"[Socket] Received raw string: {data_r_str}")

                data_dict = json.loads(data_r_str)

                ts = data_dict.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                tp = data_dict.get("temperature", "-")
                hm = data_dict.get("humidity", "-")
                co2 = data_dict.get("co2", "-")
                nm = data_dict.get("name", "-")

                row = [ts, tp, hm, co2, nm]

                save_sensor_row(row)
                print(f"[Socket] Successfully saved to CSV: {row}")

                socket_s_r.close()

            except Exception as e:
                print(f"[Socket Error] {e}")
                time.sleep(1)

