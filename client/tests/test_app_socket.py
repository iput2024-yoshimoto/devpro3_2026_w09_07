import json
import pytest
# ★ app ではなく socket_server をインポートする
from server.src import socket_server

class TestSocketServerLogic:
    def test_socket_server_receive_success(self, mocker):
        # ★ socket_server.py の中で使われている保存関数をモックする
        # (もし csv_handler から save_sensor_row をインポートして使っている場合)
        mock_csv_write = mocker.patch("server.src.socket_server.save_sensor_row") 
        
        # ※もし socket_server.py 側でまだ csv_write_iterator という名前を使っている場合は、
        # mocker.patch("server.src.socket_server.csv_write_iterator") にしてください。
        
        mock_socket_w = mocker.MagicMock()
        mock_socket_s_r = mocker.MagicMock()
        
        mock_socket_w.accept.side_effect = [
            (mock_socket_s_r, ("192.168.11.50", 12345)),
            KeyboardInterrupt("Stop loop") 
        ]
        
        mock_json_data = {
            "timestamp": "2026-07-19 22:00:00",
            "temperature": 22.5,
            "humidity": 45.2,
            "co2": 600,
            "name": "tk240110"
        }
        mock_socket_s_r.recv.return_value = json.dumps(mock_json_data).encode('utf-8')

        mocker.patch("socket.socket", return_value=mock_socket_w)

        try:
            # ★ app.socket_server_loop() ではなく socket_server.socket_server_loop()
            socket_server.socket_server_loop()
        except KeyboardInterrupt:
            pass
        
        assert mock_csv_write.called