import pytest

try:
    import client.src.dht22_takemoto as dht22
except ImportError:
    import dht22

class TestDHT22Class:
    @pytest.fixture
    def dht_instance(self, mocker):
        """lgpioをモック化したDHT22インスタンス"""
        mocker.patch("lgpio.gpiochip_open", return_value=1)
        return dht22.DHT22(gpio=26)

    def test_bits_to_bytes_conversion(self, dht_instance):
        bits = [True, False, True, False, True, False, True, False] * 5
        bytes_out = dht_instance._DHT22__bits_to_bytes(bits)
        assert bytes_out == [170, 170, 170, 170, 170]

    def test_read_negative_temperature(self, dht_instance, mocker):
        mock_bytes = [0x01, 0xF4, 0x80, 0x19, 0x8E]
        
        # mocker.patch.object で対象メソッドだけをモック化
        mocker.patch.object(dht_instance, '_DHT22__collect_input', return_value=[])
        mocker.patch.object(dht_instance, '_DHT22__parse_data_pull_up_lengths', return_value=[0]*40)
        mocker.patch.object(dht_instance, '_DHT22__calculate_bits', return_value=[True]*40)
        mocker.patch.object(dht_instance, '_DHT22__bits_to_bytes', return_value=mock_bytes)
        
        temp, hum, crc = dht_instance.read()
        assert temp == -2.5
        assert hum == 50.0

    def test_read_missing_data_error(self, dht_instance, mocker):
        mocker.patch.object(dht_instance, '_DHT22__collect_input', return_value=[])
        mocker.patch.object(dht_instance, '_DHT22__parse_data_pull_up_lengths', return_value=[0]*30)
        
        with pytest.raises(dht22.DHT22MissingDataError):
            dht_instance.read()