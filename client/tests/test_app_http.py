class TestFlaskEndpoints:

    def test_index_empty_csv(self, client_app, mocker):
        # server.src. を外して、単に "routes.xxx" とする
        mocker.patch("routes.read_all_rows", return_value=[])
        mocker.patch("routes.render_template", return_value="<html>Dummy</html>")
        
        response = client_app.get("/")
        assert response.status_code == 200

    def test_submit_success(self, client_app, mocker):
        # ここも "routes.save_sensor_row" に変更
        mock_save = mocker.patch("routes.save_sensor_row")
        
        form_data = {
            'temperature': '25.3',
            'humidity': '60.5',
            'co2': '800',
            'student_id': 'tk240006'
        }
        response = client_app.post("/submit", data=form_data)
        
        assert response.status_code == 200
        assert mock_save.called

    def test_latest_endpoint(self, client_app, mocker):
        # read_all_rows の返り値に合わせて「リストのリスト」でダミーデータを用意
        dummy_rows = [["2026-07-24 12:00:00", "26.4", "55.0", "450", "tk240006"]]
        
        # 修正：モック対象を routes.read_all_rows に変更
        mocker.patch("routes.read_all_rows", return_value=dummy_rows)

        response = client_app.get("/latest")
        
        assert response.status_code == 200
        assert "26.4" in response.data.decode('utf-8')