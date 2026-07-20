import sys
from unittest.mock import MagicMock
import pytest

# 1. ハードウェア・非対応モジュールのダミー化
sys.modules['lgpio'] = MagicMock()
sys.modules['mh_z19'] = MagicMock()

# test_socket_server 以外のテスト（test_app など）で無限ループに入るのを防止するフィクスチャ
@pytest.fixture(autouse=True)
def mock_infinite_loops(request, monkeypatch):
    """test_socket_server 以外のテスト実行時のみ socket_server_loop をモック化"""
    if "test_socket_server" not in request.node.nodeid:
        dummy_func = MagicMock()
        monkeypatch.setattr("server.src.socket_server.socket_server_loop", dummy_func, raising=False)
        monkeypatch.setattr("server.src.app.socket_server_loop", dummy_func, raising=False)