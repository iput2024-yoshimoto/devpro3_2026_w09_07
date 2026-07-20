import sys
from unittest.mock import MagicMock

# CI環境で lgpio や mh_z19 が存在しない場合にダミー（Mock）に差し替える
sys.modules['lgpio'] = MagicMock()
sys.modules['mh_z19'] = MagicMock()