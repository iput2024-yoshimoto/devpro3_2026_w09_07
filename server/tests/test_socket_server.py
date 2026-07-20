import json
import pytest
from unittest.mock import patch, MagicMock

import server.src.socket_server as socket_module

@patch("server.src.socket_server.save_sensor_row")
@patch("socket.socket")
def test_socket_server_loop_single_iteration(mock_socket_cls, mock_save_row):
    """ソケットサーバーが接続を受信し、JSONパース後にCSV保存される流れを検証"""
 
    mock_server_socket = MagicMock()
    mock_client_socket = MagicMock()
    mock_socket_cls.return_value = mock_server_socket
    
    mock_server_socket.accept.side_effect = [
        (mock_client_socket, ("127.0.0.1", 12345)),
        KeyboardInterrupt() 
    ]

    dummy_data = {
        "timestamp": "2026-01-01 12:00:00",
        "temperature": "23.5",
        "humidity": "45.0",
        "co2": "410",
        "name": "RaspberryPi_1"
    }
    mock_client_socket.recv.return_value = json.dumps(dummy_data).encode("utf-8")

    try:
        socket_module.socket_server_loop()
    except KeyboardInterrupt:
        pass

    mock_client_socket.recv.assert_called_once_with(1024)
    mock_save_row.assert_called_once_with([
        "2026-01-01 12:00:00", "23.5", "45.0", "410", "RaspberryPi_1"
    ])
    mock_client_socket.close.assert_called_once()

@patch("socket.socket")
def test_socket_server_loop_empty_recv(mock_socket_cls):
    """データが空（切断時）の場合に即座にソケットが閉じられるか検証"""
    mock_server_socket = MagicMock()
    mock_client_socket = MagicMock()
    mock_socket_cls.return_value = mock_server_socket
    
    mock_server_socket.accept.side_effect = [
        (mock_client_socket, ("127.0.0.1", 12345)),
        KeyboardInterrupt()
    ]

    mock_client_socket.recv.return_value = b""

    try:
        socket_module.socket_server_loop()
    except KeyboardInterrupt:
        pass

    mock_client_socket.close.assert_called_once()

@patch("server.src.socket_server.time.sleep")
@patch("socket.socket")
def test_socket_server_loop_handles_exception(mock_socket_cls, mock_sleep):
    """通信またはパースエラー発生時に例外が捕捉されスリープ処理に入るか検証"""
    mock_server_socket = MagicMock()
    mock_client_socket = MagicMock()
    mock_socket_cls.return_value = mock_server_socket
    
    mock_server_socket.accept.side_effect = [
        (mock_client_socket, ("127.0.0.1", 12345)),
        KeyboardInterrupt()
    ]

    mock_client_socket.recv.return_value = b"invalid_json"

    try:
        socket_module.socket_server_loop()
    except KeyboardInterrupt:
        pass

    mock_sleep.assert_called_once_with(1)