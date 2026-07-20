import sys
import pytest
from unittest.mock import MagicMock, patch

# テスト実行環境に lgpio がインストールされていなくても
# インポートエラーにならないようにモジュール全体をモック化します
sys.modules['lgpio'] = MagicMock()

# ここで元のモジュールをインポートします（ファイル名が dht22.py であることを想定）
from src import dht22_takemoto as DHT22, DHT22MissingDataError, DHT22CRCError

@pytest.fixture
def mock_lgpio():
    """lgpioのモックを提供するフィクスチャ"""
    return sys.modules['lgpio']

@pytest.fixture
def dht_sensor(mock_lgpio):
    """DHT22インスタンスを提供するフィクスチャ。テスト後にclose処理を行う"""
    # gpiochip_openの戻り値(ハンドル)をモック
    mock_lgpio.gpiochip_open.return_value = 123 
    
    sensor = DHT22(gpio=26)
    yield sensor
    sensor.close()

def generate_dummy_pull_up_lengths(h_high, h_low, t_high, t_low):
    """
    テスト用の疑似パルス幅データを生成するヘルパー関数。
    短いパルス(0)を20、長いパルス(1)を70として40ビット分の配列を作成する。
    """
    checksum = (h_high + h_low + t_high + t_low) & 0xFF
    bytes_data = [h_high, h_low, t_high, t_low, checksum]
    
    lengths = []
    for b in bytes_data:
        for i in range(7, -1, -1):
            bit = (b >> i) & 1
            lengths.append(70 if bit else 20)
    return lengths

class TestDHT22:
    def test_init_and_close(self, mock_lgpio):
        """初期化と終了処理が正しくlgpioの関数を呼び出すかテスト"""
        mock_lgpio.gpiochip_open.return_value = 99
        
        sensor = DHT22(gpio=26)
        mock_lgpio.gpiochip_open.assert_called_once_with(0)
        
        sensor.close()
        mock_lgpio.gpiochip_close.assert_called_once_with(99)

    @patch.object(DHT22, '_DHT22__collect_input')
    @patch.object(DHT22, '_DHT22__send_and_sleep')
    def test_read_success(self, mock_send, mock_collect, dht_sensor):
        """正常に温度と湿度が読み取れる場合のテスト"""
        # 湿度: 45.2% -> 452 -> 0x01, 0xC4
        # 温度: 23.5 C -> 235 -> 0x00, 0xEB
        dummy_lengths = generate_dummy_pull_up_lengths(0x01, 0xC4, 0x00, 0xEB)
        
        # タイミング制御のループをスキップし、疑似的なパルス幅データを返すようモック化
        with patch.object(DHT22, '_DHT22__parse_data_pull_up_lengths', return_value=dummy_lengths):
            temp, hum, checksum = dht_sensor.read()
            
        assert temp == 23.5
        assert hum == 45.2
        # チェックサムは 0x01 + 0xC4 + 0x00 + 0xEB = 0x1B0 -> 0xB0
        assert checksum == 0xB0

    @patch.object(DHT22, '_DHT22__collect_input')
    @patch.object(DHT22, '_DHT22__send_and_sleep')
    def test_read_negative_temperature(self, mock_send, mock_collect, dht_sensor):
        """氷点下（マイナス温度）が正しく計算されるかテスト"""
        # 湿度: 45.2% -> 0x01, 0xC4
        # 温度: -10.5 C -> 105 (0x69) | 最上位ビットON (0x80) -> 0x80, 0x69
        dummy_lengths = generate_dummy_pull_up_lengths(0x01, 0xC4, 0x80, 0x69)
        
        with patch.object(DHT22, '_DHT22__parse_data_pull_up_lengths', return_value=dummy_lengths):
            temp, hum, _ = dht_sensor.read()
            
        assert temp == -10.5
        assert hum == 45.2

    @patch.object(DHT22, '_DHT22__collect_input')
    @patch.object(DHT22, '_DHT22__send_and_sleep')
    def test_missing_data_error(self, mock_send, mock_collect, dht_sensor):
        """データが40ビット分取得できなかった場合に例外が発生するかテスト"""
        # 39個しかデータがない状態を意図的に作成
        dummy_lengths = [20] * 39 
        
        with patch.object(DHT22, '_DHT22__parse_data_pull_up_lengths', return_value=dummy_lengths):
            with pytest.raises(DHT22MissingDataError):
                dht_sensor.read()

    @patch.object(DHT22, '_DHT22__collect_input')
    @patch.object(DHT22, '_DHT22__send_and_sleep')
    def test_crc_error(self, mock_send, mock_collect, dht_sensor):
        """チェックサムが合わない場合に例外が発生するかテスト"""
        dummy_lengths = generate_dummy_pull_up_lengths(0x01, 0xC4, 0x00, 0xEB)
        # 最後の1ビットを反転させて意図的にCRCエラーを引き起こす
        dummy_lengths[-1] = 70 if dummy_lengths[-1] == 20 else 20
        
        with patch.object(DHT22, '_DHT22__parse_data_pull_up_lengths', return_value=dummy_lengths):
            with pytest.raises(DHT22CRCError):
                dht_sensor.read()

    def test_calculate_checksum_internal(self, dht_sensor):
        """内部メソッド __calculate_checksum のロジックテスト"""
        # 0x01 + 0xC4 + 0x00 + 0xEB = 0x1B0 -> 0xB0
        test_bytes = [0x01, 0xC4, 0x00, 0xEB, 0x00]  # 最後の要素は計算に使われない
        result = dht_sensor._DHT22__calculate_checksum(test_bytes)
        assert result == 0xB0

    def test_bits_to_bytes_internal(self, dht_sensor):
        """内部メソッド __bits_to_bytes のロジックテスト"""
        # 0xC4 (11000100) と 0x03 (00000011) を表すブール配列
        test_bits = [
            True, True, False, False, False, True, False, False,  # 0xC4
            False, False, False, False, False, False, True, True   # 0x03
        ]
        result = dht_sensor._DHT22__bits_to_bytes(test_bits)
        assert result == [0xC4, 0x03]