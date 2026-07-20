# conftest.py
import sys
from unittest.mock import MagicMock

# --- PCやCI/CD環境（Raspberry Pi以外）向けの lgpio 事前モック化 ---
if "lgpio" not in sys.modules:
    mock_lgpio = MagicMock()
    # ライブラリ内で参照されている定数をセットアップ
    mock_lgpio.SET_PULL_UP = 1
    mock_lgpio.LGPIO_PULL_UP = 1
    sys.modules["lgpio"] = mock_lgpio