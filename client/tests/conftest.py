import os
import sys
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Flaskアプリやその他のモジュールが読み込まれる前に環境変数をセット
os.environ.setdefault("WAITING_PORT", "8765")
os.environ.setdefault("SERVER_IP", "10.192.137.123")
os.environ.setdefault("TEMPLATE_NAME", "HTML_iteration_g7.html")



# パスと環境変数が設定された後で、Flaskアプリの本体をインポートします
# ※実際のFlaskアプリ (app = Flask(__name__)) が定義されている場所に合わせて変更してください
from server.src.app import app 

@pytest.fixture
def client_app():
    """
    Flaskのテスト用クライアントを提供するFixture。
    テスト関数の引数に client_app と書くだけで HTTPリクエストのテストが可能になります。
    """
    # テストモードを有効化（エラーの詳細が出やすくなりす）
    app.config.update({
        "TESTING": True,
    })
    
    with app.test_client() as client:
        yield client