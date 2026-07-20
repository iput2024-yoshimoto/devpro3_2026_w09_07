import sys
from unittest.mock import MagicMock
import pytest

# 1. ハードウェア・非対応モジュールのダミー化
sys.modules['lgpio'] = MagicMock()
sys.modules['mh_z19'] = MagicMock()

# 2. 自動モック（すべてのテストでソケットサーバー等のループ関数を安全に無効化）
@pytest.fixture(autouse=True)
def mock_infinite_loops(monkeypatch):
    """ソケットサーバー等の無限ループ処理を安全なダミー関数に自動差し替え"""
    dummy_func = MagicMock()
    
    # socket_server モジュールのループ処理をモック化
    monkeypatch.setattr("server.src.socket_server.socket_server_loop", dummy_func, raising=False)
    monkeypatch.setattr("server.src.app.socket_server_loop", dummy_func, raising=False)