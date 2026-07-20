import pytest
from unittest.mock import patch, mock_open, MagicMock
import server.src.csv_handler as csv_handler

def test_save_sensor_row():
    """CSVへ行データが正しく追記保存されるか検証"""
    row_data = ["2026-01-01 10:00:00", "25.0", "50.0", "400", "Student_A"]
    
    # csv.writer をモック化して内部の writerow 呼び出しを検証する
    mock_writer_instance = MagicMock()
    
    with patch.object(csv_handler, "ensure_data_dir"), \
         patch("builtins.open", mock_open()), \
         patch("csv.writer", return_value=mock_writer_instance):
        
        csv_handler.save_sensor_row(row_data)
        
        # writerow が正しいデータで呼ばれたか検証
        mock_writer_instance.writerow.assert_called_once_with(row_data)