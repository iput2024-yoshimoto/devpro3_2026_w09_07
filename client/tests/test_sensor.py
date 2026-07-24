import client.src.get_co2_data
import sensor

class TestSensorModules:
    def test_get_co2_data_success(self, mocker):
        # サブプロセスをモックして実際のコマンド実行を防ぐ
        mocker.patch("subprocess.check_output", return_value=b'{"co2": 500}')
        res = client.src.get_co2_data.get_co2_data()
        assert res == 500

    def test_get_co2_data_failure(self, mocker):
        mocker.patch("subprocess.check_output", side_effect=Exception("Command error"))
        res = client.src.get_co2_data.get_co2_data()
        assert res == -1

    def test_main_loop_one_cycle(self, mocker):
        mock_get_co2 = mocker.patch("sensor.get_co2_data", return_value=400)
        
        # 1周目で強制終了させるために例外を投げる
        mock_send_server = mocker.patch("sensor.send_data_to_server", side_effect=KeyboardInterrupt("Stop loop"))
        
        # 無限ループでの待機時間をゼロにする
        mocker.patch("time.sleep")

        try:
            sensor.main_loop("localhost", 8765)
        except KeyboardInterrupt:
            pass

        # DHTの確認を削除し、代わりにCO2が呼ばれたかを確認
        assert mock_get_co2.called
        assert mock_send_server.called