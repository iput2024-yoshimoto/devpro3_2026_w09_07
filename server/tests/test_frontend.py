import pytest
from server.src.app import create_app

@pytest.fixture
def client():
    """テスト用のFlaskクライアントを生成"""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_html_structure(client):
    """メイン画面(/)にアクセスした際、200 OKが返り、HTMLの基本要素が存在するか検証"""
    response = client.get("/")
    assert response.status_code == 200
    
    # レスポンス本文にHTML要素や必要なIDが含まれているか確認
    html = response.data.decode("utf-8")
    assert "<!DOCTYPE html>" in html or "<html" in html
    assert 'id="last-update"' in html
    assert 'id="sensor-form"' in html

def test_static_js_file_exists(client):
    """staticフォルダ内のJavaScriptファイルが404にならず取得できるか検証"""
    response = client.get("/static/Java_iteration_g7.js")
    
    assert response.status_code == 200
    assert "javascript" in response.headers["Content-Type"]