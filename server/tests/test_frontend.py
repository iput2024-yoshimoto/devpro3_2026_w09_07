import pytest
from unittest.mock import patch

def test_index_html_structure(client_app):
    """HTMLが正しくレンダリングされ、必要なIDやクラスが存在するか検証"""
    # テスト用のダミーセンサーデータを用意
    dummy_data = [
        ["2026-07-23 10:00:00", "25.5", "55.0", "600", "TK240006"],
        ["2026-07-23 11:00:00", "26.0", "62.0", "1050", "TK240006"]
    ]

    # render_template に dummy_data を渡すようにモック/コンテキスト設定
    with patch("app2.render_template") as mock_render:
        mock_render.return_value = """
        <span id="avg-temp">--.-</span>
        <span id="avg-humid">--.-</span>
        <span id="avg-co2">----</span>
        <form id="sensor-form"></form>
        <tbody id="data-tbody">
            <tr class="data-row">
                <td class="temp-cell">25.5</td>
                <td class="humid-cell">55.0</td>
                <td class="co2-cell">600</td>
            </tr>
        </tbody>
        <div id="warning-msg" class="hidden"></div>
        """
        response = client_app.get("/")
        assert response.status_code == 200

def test_static_js_file_exists(client_app):
    """staticフォルダから JavaScript ファイルが正常に読み込めるか検証"""
    # JSファイル名: Java_iteration_g7.js
    response = client_app.get("/static/Java_iteration_g7.js")
    
    # ファイルが存在すれば 200 OK、JavaScriptの Content-Type が返る
    assert response.status_code == 200
    assert "javascript" in response.headers["Content-Type"]