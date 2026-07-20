import sys
from unittest.mock import MagicMock

# CI環境で mh_z19 や lgpio が見つからない場合に備えてモック化
sys.modules['mh_z19'] = MagicMock()