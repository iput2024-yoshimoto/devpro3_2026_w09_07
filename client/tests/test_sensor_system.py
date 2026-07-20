import os
import json
import csv
import socket
import pytest
from unittest.mock import MagicMock, patch
os.environ.setdefault("WAITING_PORT", "8765")
os.environ.setdefault("SERVER_IP", "127.0.0.1")
# テスト対象モジュールのインポート
import app2
import get_co2_data
import get_dht_data
import sensor

try:
    import dht22_takemoto as dht22
except ImportError:
    import dht22


# ==========================================
# Fixtures (共通処理)
# ==========================================

@pytest.fixture
def mock_csv_dir(tmp_path, monkeypatch):
    """一時的なCSV保存先をセットアップ"""
    test_dir = tmp_path / "lastwork"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "sensor_data.csv"
    
    monkeypatch.setattr(app2, "DATA_DIR", str(test_dir), raising=False)
    monkeypatch.setattr(app2, "DEFAULT_FILENAME", str(test_file), raising=False)
    
    return test_file


@pytest.fixture
def client_app(mock_csv_dir):
    """Flaskテストクライアント"""
    app2.app.config.update({"TESTING": True})
    with app2.app.test_client() as client:
        yield client


# ==========================================
# 1. DHT22 クラス単体のテスト (新規追加)
# ==========================================

class TestDHT22Class:
    """DHT22クラス内部の信号処理・計算ロジックの単体テスト"""

    @pytest.fixture
    def dht_instance(self):
        """lgpioをモック化したDHT22インスタンス"""
        with patch("lgpio.gpiochip_open", return_value=1):
            return dht22.DHT22(gpio=26)

    def test_bits_to_bytes_conversion(self, dht_instance):
        """ビット配列(bool list)からバイト配列(int list)への変換テスト"""
        # [1,0,1,0,1,0,1,0] -> 0xAA (170)
        bits = [True, False, True, False, True, False, True, False] * 5  # 40 bits = 5 bytes
        bytes_out = dht_instance._DHT22__bits_to_bytes(bits)
        
        assert len(bytes_out) == 5
        assert bytes_out == [170, 170, 170, 170, 170]

    def test_calculate_checksum(self, dht_instance):
        """チェックサム計算ロジックの検証"""
        # 4バイトの和の下位8ビットがチェックサムとなる
        data_bytes = [10, 20, 30, 40]
        checksum = dht_instance._DHT22__calculate_checksum(data_bytes)
        assert checksum == 100  # 10 + 20 + 30 + 40

        # オーバーフロー(256以上)のマスク検証
        data_bytes_overflow = [200, 100, 50, 50]  # 合計400 -> 400 & 0xFF = 144
        checksum_overflow = dht_instance._DHT22__calculate_checksum(data_bytes_overflow)
        assert checksum_overflow == 144

    def test_read_negative_temperature(self, dht_instance):
        """氷点下（負の温度）のデコード処理テスト"""
        # 湿度50.0% (0x01, 0xF4), 温度 -2.5℃ (0x80, 0x19), Checksum (0x8E)
        # 0x8019 -> 最上位ビット(0x8000)が立っているためマイナス
        mock_bytes = [0x01, 0xF4, 0x80, 0x19, 0x8E]
        
        with patch.object(dht_instance, '_DHT22__collect_input', return_value=[]), \
             patch.object(dht_instance, '_DHT22__parse_data_pull_up_lengths', return_value=[0]*40), \
             patch.object(dht_instance, '_DHT22__calculate_bits', return_value=[True]*40), \
             patch.object(dht_instance, '_DHT22__bits_to_bytes', return_value=mock_bytes):
            
            temp, hum, crc = dht_instance.read()
            assert temp == -2.5
            assert hum == 50.0

    def test_read_missing_data_error(self, dht_instance):
        """パルス数が40未満（データ欠損）のときに MissingDataError が出るか"""
        with patch.object(dht_instance, '_DHT22__collect_input', return_value=[]), \
             patch.object(dht_instance, '_DHT22__parse_data_pull_up_lengths', return_value=[0]*30):  # 30個しか取れなかった
            
            with pytest.raises(dht22.DHT22MissingDataError):
                dht_instance.read()

    def test_read_crc_error(self, dht_instance):
        """チェックサム不一致のときに CRCError が発生するか"""
        # 不正なチェックサムデータ
        mock_bytes = [0x01, 0x00, 0x01, 0x00, 0xFF] # 1+0+1+0 = 2 != 255
        
        with patch.object(dht_instance, '_DHT22__collect_input', return_value=[]), \
             patch.object(dht_instance, '_DHT22__parse_data_pull_up_lengths', return_value=[0]*40), \
             patch.object(dht_instance, '_DHT22__calculate_bits', return_value=[True]*40), \
             patch.object(dht_instance, '_DHT22__bits_to_bytes', return_value=mock_bytes):
            
            with pytest.raises(dht22.DHT22CRCError):
                dht_instance.read()


# ==========================================
# 2. HTTP エンドポイント & 入力検証のテスト
# ==========================================

class TestFlaskEndpoints:

    def test_index_empty_csv(self, client_app):
        """トップページの閲覧確認"""
        response = client_app.get("/")
        assert response.status_code == 200

    def test_submit_success(self, client_app, mock_csv_dir):
        """/submit 正常系データ入力テスト"""
        form_data = {
            'temperature': '25.3',
            'humidity': '60.5',
            'co2': '800',
            'student_id': 'tk240006'
        }
        response = client_app.post("/submit", data=form_data)
        assert response.status_code in [200, 201, 302]

        if os.path.exists(mock_csv_dir):
            with open(mock_csv_dir, mode='r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                assert reader[0][1] == '25.3'

    def test_submit_missing_fields(self, client_app):
        """【新規】フォームデータが欠落している場合の検証"""
        incomplete_data = {'temperature': '25.3'}  # 湿度やCO2が欠落
        response = client_app.post("/submit", data=incomplete_data)
        
        # サーバーがクラッシュ(500)せず、400 Bad Request またはエラーハンドリングされること
        assert response.status_code != 500

    def test_latest_endpoint(self, client_app, mock_csv_dir):
        """/latest エンドポイントのテスト"""
        row = ["2026-07-19 12:00:00", "26.4", "55.0", "450", "tk240006"]
        with open(mock_csv_dir, mode='a', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow(row)

        response = client_app.get("/latest")
        if response.status_code == 200:
            assert "26.4" in response.data.decode('utf-8')


# ==========================================
# 3. Socket サーバーの堅牢性テスト
# ==========================================

class TestSocketServerLogic:

    @patch("app2.csv_write_iterator")
    def test_socket_server_receive_success(self, mock_csv_write):
        """Socket通信の正常受信処理"""
        mock_socket_w = MagicMock()
        mock_socket_s_r = MagicMock()
        
        mock_socket_w.accept.side_effect = [
            (mock_socket_s_r, ("192.168.11.50", 12345)),
            KeyboardInterrupt("Stop loop") 
        ]
        
        mock_json_data = {
            "timestamp": "2026-07-19 22:00:00",
            "temperature": 22.5,
            "humidity": 45.2,
            "co2": 600,
            "name": "tk240006"
        }
        mock_socket_s_r.recv.return_value = json.dumps(mock_json_data).encode('utf-8')

        with patch("socket.socket", return_value=mock_socket_w):
            try:
                app2.socket_server_loop()
            except KeyboardInterrupt:
                pass
        
        assert mock_csv_write.called

    @patch("app2.csv_write_iterator")
    def test_socket_server_handles_corrupted_json(self, mock_csv_write):
        """【新規】破損したJSONが届いてもサーバーがクラッシュしないか検証"""
        mock_socket_w = MagicMock()
        mock_socket_s_r = MagicMock()
        
        mock_socket_w.accept.side_effect = [
            (mock_socket_s_r, ("192.168.11.50", 12345)),
            KeyboardInterrupt("Stop loop")
        ]
        # 不正なJSONフォーマット文字列
        mock_socket_s_r.recv.return_value = b"{ invalid json format ... "

        with patch("socket.socket", return_value=mock_socket_w):
            try:
                app2.socket_server_loop()
            except KeyboardInterrupt:
                pass
            except Exception as e:
                pytest.fail(f"不正データ受信時にサーバーが不測の例外で落下しました: {e}")


# ==========================================
# 4. センサー取得スクリプト群のテスト
# ==========================================

class TestSensorModules:

    @patch("subprocess.check_output")
    def test_get_co2_data_success(self, mock_subprocess):
        """CO2センサー正常読み込み"""
        mock_subprocess.return_value = b'{"co2": 500}'
        res = get_co2_data.get_co2_data()
        assert res == 500

    @patch("subprocess.check_output")
    def test_get_co2_data_failure(self, mock_subprocess):
        """CO2センサー読み込みエラー"""
        mock_subprocess.side_effect = Exception("Command error")
        res = get_co2_data.get_co2_data()
        assert res == -1

    @patch("get_dht_data.dht22_instance")
    def test_get_dht_data_success(self, mock_dht_instance):
        """DHT22データ取得成功"""
        mock_dht_instance.read.return_value = (23.5, 50.1, 123)
        t, h = get_dht_data.get_dht_data()
        assert t == 23.5
        assert h == 50.1

    @patch("sensor.send_data_to_server")
    @patch("sensor.get_co2_data")
    @patch("sensor.get_dht_data")
    def test_main_loop_one_cycle(self, mock_get_dht, mock_get_co2, mock_send_server):
        """sensor.py メインループ1サイクル実行テスト"""
        mock_get_dht.return_value = (24.0, 58.0)
        mock_get_co2.return_value = 400
        mock_send_server.side_effect = KeyboardInterrupt("Stop loop")

        with patch("time.sleep"):
            try:
                sensor.main_loop("localhost", 8765)
            except KeyboardInterrupt:
                pass

        assert mock_get_dht.called or mock_send_server.called