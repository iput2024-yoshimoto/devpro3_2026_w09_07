import os
import json
import csv
import socket
import pytest
from unittest.mock import MagicMock, patch

# テスト対象の Flask アプリ（app2.py）をインポート
import app2

@pytest.fixture
def mock_csv_dir(tmp_path):
    """テスト用に一時的なデータディレクトリとCSVファイルパスを書き換える"""
    test_dir = tmp_path / "lastwork"
    test_dir.mkdir()
    test_file = test_dir / "sensor_data.csv"
    
    # 元のグローバル変数をテスト用パスに差し替え
    old_dir = app2.DATA_DIR
    old_file = app2.DEFAULT_FILENAME
    app2.DATA_DIR = str(test_dir)
    app2.DEFAULT_FILENAME = str(test_file)
    
    yield test_file
    
    # テスト終了後に元に戻す
    app2.DATA_DIR = old_dir
    app2.DEFAULT_FILENAME = old_file

@pytest.fixture
def client_app(mock_csv_dir):
    """Flaskのテストクライアント"""
    app2.app.config.update({"TESTING": True})
    with app2.app.test_client() as client:
        yield client

# --- HTTPエンドポイントのテスト ---
class TestFlaskEndpoints:

    def test_index_empty_csv(self, client_app):
        """CSVが存在しない、または空の時のメイン画面アクセス"""
        response = client_app.get("/")
        assert response.status_code == 200
        assert b"html" in response.data.lower()

    def test_submit_success(self, client_app, mock_csv_dir):
        """/submit へのPOSTリクエストによるCSV書き込みテスト"""
        form_data = {
            'temperature': '25.3',
            'humidity': '60.5',
            'co2': '800',
            'student_id': 'tk240006'
        }
        response = client_app.post("/submit", data=form_data)
        assert response.status_code == 200
        assert response.data == b"Success"

        # CSV正しく書き込まれたか確認
        with open(mock_csv_dir, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            assert len(reader) == 1
            assert reader[0][1] == '25.3'  # 温度
            assert reader[0][2] == '60.5'  # 湿度
            assert reader[0][3] == '800'   # CO2
            assert reader[0][4] == 'tk240006' # 学籍番号

    def test_latest_endpoint(self, client_app, mock_csv_dir):
        """/latest から最新の1件がプレーンテキストで取得できるかテスト"""
        row = ["2026-07-19 12:00:00", "26.4", "55.0", "450", "tk240006"]
        app2.csv_write_iterator(row)

        response = client_app.get("/latest")
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/plain'
        assert response.data.decode('utf-8') == ",".join(row)

    def test_latest_no_data(self, client_app):
        """CSVデータがない場合の /latest の挙動テスト"""
        response = client_app.get("/latest")
        assert response.status_code == 404
        assert response.data == b"No data available"

# --- Socketサーバー内部ロジックのテスト ---
class TestSocketServerLogic:

    @patch("app2.csv_write_iterator")
    def test_socket_server_loop_single_receive(self, mock_csv_write):
        """Socket通信を受け取った際のパースとCSV保存ロジックのテスト"""
        mock_socket_w = MagicMock()
        mock_socket_s_r = MagicMock()
        
        # 1回目はデータ受信、2回目でループを抜けるためにKeyboardInterruptを起こす
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
            with pytest.raises(KeyboardInterrupt):
                app2.socket_server_loop()
        
        # HTML/JS側の想定に合わせた並び順 [時刻, 温度, 湿度, CO2, 学籍番号]
        mock_csv_write.assert_called_once_with([
            "2026-07-19 22:00:00", 22.5, 45.2, 600, "tk240006"
        ])
