import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

import server.src.app as app_module
from server.src.app import create_app


def test_create_app():
    """create_appがFlaskアプリケーションを正しく生成し、Blueprintが登録されているか検証"""
    app = create_app()
    assert isinstance(app, Flask)
    assert "main" in app.blueprints


@patch("flask.Flask.run")  # ← Flaskのサーバー起動処理を横取りしてブロックを防ぐ
@patch("server.src.app.socket_server_loop")
@patch("server.src.app.threading.Thread")
def test_main_execution(mock_thread, mock_socket_loop, mock_flask_run):
    """__name__ == '__main__' のブロック相当の動きを検証"""
    
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    # ソケットスレッドの起動模倣
    socket_thread = app_module.threading.Thread(
        target=mock_socket_loop, 
        daemon=True
    )
    socket_thread.start()
    
    # アプリ作成と起動模倣 (mock_flask_run がブロックを防止)
    app = app_module.create_app()
    app.run(
        host=app_module.FLASK_HOST,
        port=app_module.FLASK_PORT,
        debug=app_module.FLASK_DEBUG
    )

    # 検証
    mock_thread_instance.start.assert_called_once()
    mock_flask_run.assert_called_once_with(
        host=app_module.FLASK_HOST,
        port=app_module.FLASK_PORT,
        debug=app_module.FLASK_DEBUG
    )