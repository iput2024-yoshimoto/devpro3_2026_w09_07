import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

# テスト対象モジュールのインポート（パスは適宜プロジェクトに合わせて変更してください）
import server.src.app as app_module
from server.src.app import create_app

def test_create_app():
    """create_appがFlaskアプリケーションを正しく生成し、Blueprintが登録されているか検証"""
    app = create_app()
    assert isinstance(app, Flask)
    assert "main" in app.blueprints

@patch("app.threading.Thread")
@patch("app.create_app")
def test_main_execution(mock_create_app, mock_thread):
    """__name__ == '__main__' のブロックが正常にスレッドとFlaskを起動するか検証"""
    mock_app_instance = MagicMock()
    mock_create_app.return_value = mock_app_instance
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance


    with patch.object(app_module, "__name__", "__main__"):

        socket_thread = app_module.threading.Thread(
            target=app_module.socket_server_loop, 
            daemon=True
        )
        socket_thread.start()
        
        flask_app = app_module.create_app()
        flask_app.run(
            host=app_module.FLASK_HOST,
            port=app_module.FLASK_PORT,
            debug=app_module.FLASK_DEBUG
        )

    mock_thread_instance.start.assert_called_once()
    mock_app_instance.run.assert_called_once_with(
        host=app_module.FLASK_HOST,
        port=app_module.FLASK_PORT,
        debug=app_module.FLASK_DEBUG
    )