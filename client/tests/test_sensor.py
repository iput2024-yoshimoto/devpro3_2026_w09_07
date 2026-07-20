import pytest
from unittest.mock import MagicMock, patch

import get_co2_data
import get_dht_data
import sensor
import dht22_takemoto as dht22


class TestSensorModules:

    @patch("subprocess.check_output")
    def test_get_co2_data_success(self, mock_subprocess):
        """MH-Z19C から正常にCO2データが取得できた場合"""
        mock_subprocess.return_value = b"{'co2': 500}"
        res = get_co2_data.get_co2_data()
        assert res == 500

    @patch("subprocess.check_output")
    def test_get_co2_data_failure(self, mock_subprocess):
        """MH-Z19C のエラー発生時、-1 を返すかテスト"""
        mock_subprocess.side_effect = Exception("Command error")
        res = get_co2_data.get_co2_data()
        assert res == -1

    @patch("get_dht_data.dht22_instance")
    def test_get_dht_data_success(self, mock_dht_instance):
        """get_dht_data が正常に温湿度を返すかテスト"""
        mock_dht_instance.read.return_value = (23.5, 50.1, 123)
        t, h = get_dht_data.get_dht_data()
        assert t == 23.5
        assert h == 50.1

    @patch("sensor.dht22_instance")
    def test_sensor_script_get_dht_data_crc_error(self, mock_dht_instance):
        """sensor.py 側で発生する CRCエラーのハンドリングテスト"""
        mock_dht_instance.read.side_effect = dht22.DHT22CRCError()
        
        # sensor.py の get_dht_data はエラー時に例外を再送出する仕様
        with patch("time.sleep"):  # テスト高速化のためにsleepを無効化
            with pytest.raises(dht22.DHT22CRCError):
                sensor.get_dht_data()

    @patch("sensor.send_data_to_server")
    @patch("sensor.get_co2_data")
    @patch("sensor.get_dht_data")
    def test_main_loop_one_cycle(self, mock_get_dht, mock_get_co2, mock_send_server):
        """sensor.py のメインループが1サイクル正しく回るかテスト"""
        mock_get_dht.return_value = (24.0, 58.0)
        mock_get_co2.return_value = 400
        mock_send_server.side_effect = KeyboardInterrupt("Stop loop")

        # time.sleep とソケット送信関連の例外抜けを防止
        with patch("time.sleep"):
            try:
                sensor.main_loop("localhost", 8765)
            except KeyboardInterrupt:
                pass  # KeyboardInterrupt をキャッチして正常終了とみなす

        # 送信関数または取得関数が呼び出されたことを検証
        assert mock_get_dht.called or mock_send_server.called