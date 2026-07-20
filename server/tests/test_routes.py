import pytest
from unittest.mock import patch
from flask import Flask
from server.src.routes import main_bp

@pytest.fixture
def client():
    """Flaskテスト用クライアントフィクスチャ"""
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# --- GET / のテスト ---
@patch("server.src.routes.render_template")
@patch("server.src.routes.read_all_rows")
def test_index_route(mock_read_all, mock_render_template, client):
    """GET / が正常にデータを取得しテンプレートをレンダリングするか検証"""
    mock_read_all.return_value = [["2026-01-01", "25", "50", "400", "Test"]]
    mock_render_template.return_value = "Rendered HTML"

    response = client.get("/")
    
    assert response.status_code == 200
    mock_read_all.assert_called_once()
    mock_render_template.assert_called_once()

# --- POST /submit のテスト ---
@patch("server.src.routes.save_sensor_row")
def test_submit_route_success(mock_save, client):
    """POST /submit でフォームデータが送られた際、正常に保存され200が返るか検証"""
    form_data = {
        "temperature": "26.5",
        "humidity": "55.0",
        "co2": "450",
        "student_id": "ST123"
    }
    response = client.post("/submit", data=form_data)
    
    assert response.status_code == 200
    assert response.data.decode("utf-8") == "Success"
    assert mock_save.called
    saved_row = mock_save.call_args[0][0]
    assert saved_row[1:] == ["26.5", "55.0", "450", "ST123"]

@patch("server.src.routes.save_sensor_row")
def test_submit_route_missing_fields(mock_save, client):
    """一部のフォームデータが欠落している場合デフォルト値('-')がセットされるか検証"""
    response = client.post("/submit", data={})
    
    assert response.status_code == 200
    saved_row = mock_save.call_args[0][0]
    assert saved_row[1:] == ["-", "-", "-", "-"]

@patch("server.src.routes.save_sensor_row", side_effect=Exception("Database Error"))
def test_submit_route_exception(mock_save, client):
    """内部例外発生時に500エラーが返るか検証"""
    response = client.post("/submit", data={})
    assert response.status_code == 500
    assert "Internal Server Error" in response.data.decode("utf-8")

# --- GET /latest のテスト ---
@patch("server.src.routes.get_latest_row")
def test_latest_route_success(mock_get_latest, client):
    """最新データが存在する場合、カンマ区切り文字列と200 OKが返るか検証"""
    mock_get_latest.return_value = ["2026-01-01 12:00", "24.0", "50.0", "420", "ID01", "extra_field"]
    
    response = client.get("/latest")
    
    assert response.status_code == 200
    assert "text/plain" in response.headers["Content-Type"]
    assert response.data.decode("utf-8") == "2026-01-01 12:00,24.0,50.0,420,ID01"

@patch("server.src.routes.get_latest_row")
def test_latest_route_no_data(mock_get_latest, client):
    """データが存在しない場合、404 Not Found が返るか検証"""
    mock_get_latest.return_value = None
    
    response = client.get("/latest")
    
    assert response.status_code == 404
    assert "No data available" in response.data.decode("utf-8")

@patch("server.src.routes.get_latest_row")
def test_latest_route_insufficient_columns(mock_get_latest, client):
    """最新データの要素数が5未満の場合、404 Not Found が返るか検証"""
    mock_get_latest.return_value = ["2026-01-01 12:00", "24.0"]
    
    response = client.get("/latest")
    
    assert response.status_code == 404