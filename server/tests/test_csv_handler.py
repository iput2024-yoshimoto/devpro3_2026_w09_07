import pytest
from unittest.mock import patch, mock_open, MagicMock
import server.src.csv_handler as csv_handler

def test_ensure_data_dir():
    """ディレクトリ存在チェックと作成処理のテスト"""
    with patch("os.path.exists", return_value=False), \
         patch("os.makedirs") as mock_makedirs:
        csv_handler.ensure_data_dir()
        mock_makedirs.assert_called_once()

def test_save_sensor_row():
    """CSVへ行データが正しく追記保存されるか検証"""
    row_data = ["2026-01-01 10:00:00", "25.0", "50.0", "400", "Student_A"]
    mock_writer_instance = MagicMock()
    
    with patch.object(csv_handler, "ensure_data_dir"), \
         patch("builtins.open", mock_open()), \
         patch("csv.writer", return_value=mock_writer_instance):
        
        csv_handler.save_sensor_row(row_data)
        mock_writer_instance.writerow.assert_called_once_with(row_data)

def test_read_all_rows_file_exists():
    """CSVが存在する場合の読み込みテスト"""
    mock_data = "2026-01-01,25.0,50.0,400,ID\n2026-01-02,26.0,51.0,410,ID\n"
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)):
        rows = csv_handler.read_all_rows()
        assert len(rows) == 2
        assert rows[0] == ["2026-01-01", "25.0", "50.0", "400", "ID"]

def test_read_all_rows_file_not_exists():
    """CSVが存在しない場合は空配列が返るかテスト"""
    with patch("os.path.exists", return_value=False):
        rows = csv_handler.read_all_rows()
        assert rows == []

def test_get_latest_row_success():
    """最新の1行が正しく取得できるかテスト"""
    mock_data = "2026-01-01,25.0\n2026-01-02,26.0\n"
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)):
        latest = csv_handler.get_latest_row()
        assert latest == ["2026-01-02", "26.0"]

def test_get_latest_row_empty_file():
    """空ファイルの場合は None が返るかテスト"""
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="")):
        latest = csv_handler.get_latest_row()
        assert latest is None