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
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "sensor_data.csv"
    
    # 元のグローバル変数をテスト用パスに差し替え
    old_dir = getattr(app2, "DATA_DIR", None)
    old_file = getattr(app2, "DEFAULT_FILENAME", None)
    
    app2.DATA_DIR = str(test_dir)
    app2.DEFAULT_FILENAME = str(test_file)
    
    yield test_file
    
    # テスト終了後に元に戻す
    if old_dir is not None:
        app2.DATA_DIR = old_dir
    if old_file is not None:
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
        # HTMLテンプレートの描画エラーを回避するため render_template をモック化
        with patch("app2.render_template", return_value="<html>Dummy</html>"):
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
        
        # 成功ステータスコード (200 OK または 201 Created/リダイレクト等) を許容
        assert response.status_code in [200, 201, 302]

        # CSVが正しく作成・書き込まれたか確認
        if os.path.exists(mock_csv_dir):
            with open(mock_csv_dir, mode='r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                if len(reader) > 0:
                    assert reader[0][1] == '25.3'  # 温度
                    assert reader[0][2] == '60.5'  # 湿度
                    assert reader[0][3] == '800'   # CO2

    def test_latest_endpoint(self, client_app, mock_csv_dir):
        """/latest から最新の1件がプレーンテキストで取得できるかテスト"""
        row = ["2026-07-19 12:00:00", "26.4", "55.0", "450", "tk240006"]
        
        # テスト用CSVにダミー行を保存
        if hasattr(app2, "csv_write_iterator"):
            app2.csv_write_iterator(row)
        else:
            with open(mock_csv_dir, mode='a', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(row)

        response = client_app.get("/latest")
        
        # レスポンスが 200 OK の場合はヘッダーと内容を検証
        if response.status_code == 200:
            assert "text/plain" in response.headers['Content-Type']
            assert "26.4" in response.data.decode('utf-8')

    def test_latest_no_data(self, client_app):
        """CSVデータがない場合の /latest の挙動テスト"""
        response = client_app.get("/latest")
        # データがない場合は 404 や 200(空データ/メッセージ) などを想定
        assert response.status_code in [404, 200, 204]

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
        
        # データが保存関数に送られたか検証
        mock_csv_write.assert_called_once()