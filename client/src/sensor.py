import sys
import dht22_takemoto as dht22
import time
import datetime
import json
import socket
import config
# ↓CO2センサー用のモジュールをインポート（環境に合わせてファイル名を変更してください）
from get_co2_data import get_co2_data 

SERVER = config.SERVER # 受信サーバのIPアドレス
WAITING_PORT = int(config.WAITING_PORT)
NAME = config.NAME

WAIT_INTERVAL_RETRY = 5
WAIT_INTERVAL = 10 # サーバへの負荷を考慮し、送信間隔を少し長め(10秒など)にするのがおすすめです

# --- 温度・湿度取得 ---
dht22_instance = dht22.DHT22(gpio=26)
def get_dht_data():
    tempe = 200.0
    hum = 100.0
    try:
        tempe, hum, check = dht22_instance.read()
        print('Temperature: %-3.1f C' % tempe)
        print('Humidity: %-3.1f %%' % hum)
    except dht22.DHT22CRCError:
        print('DHT22CRCError: ' + str(datetime.datetime.now()))
        time.sleep(WAIT_INTERVAL_RETRY)
        raise(dht22.DHT22CRCError)
    except dht22.DHT22MissingDataError:
        print('DHT22MissingDataError: ' + str(datetime.datetime.now()))
        time.sleep(WAIT_INTERVAL_RETRY)
        raise(dht22.DHT22MissingDataError)
    return float(tempe), float(hum)

# --- サーバへデータ送信 ---
def send_data_to_server(hostname, port, message):
    try:
        socket_r_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_r_s.connect((hostname, port))
        data_s = message.encode('utf-8')
        socket_r_s.send(data_s)
        print(f'Sent to {hostname}:{port}')
        socket_r_s.close()
    except Exception as e:
        print(f"Connection failed: {e}")

# --- メインループ ---
def main_loop(hostname, port):
    print(f"Connecting to Server: {hostname}:{port}")
    while True: 
        try:
            # 1. センサーからデータを取得
            t, h = get_dht_data()
            co2 = get_co2_data() # CO2データを取得
            
            # 2. JSONデータを作成（サーバ側の受信フォーマットに合わせる）
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_dict = {
                "timestamp" : now_str,
                "temperature": t,
                "humidity" : h,
                "name" : NAME,
                "co2" : co2     # CO2データを追加
    
            }
            json_message = json.dumps(data_dict)
            
            # 3. サーバへ送信
            send_data_to_server(hostname, port, json_message)
            
        except (dht22.DHT22CRCError, dht22.DHT22MissingDataError):
            print("Sensor Error occurred. Skipping this cycle...")
        except KeyboardInterrupt:
            print("\nStopped by User.")
            break
        except Exception as e:
            print(f"Unexpected Error: {e}")

        time.sleep(WAIT_INTERVAL)

if __name__ == '__main__':
    main_loop(SERVER, WAITING_PORT)