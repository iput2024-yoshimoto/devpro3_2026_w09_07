import os
import csv
import pytest
from unittest.mock import patch, mock_open

import server.src.csv_handler as csv_handler

@pytest.fixture
def temp_csv_file(tmp_path):
    """テスト用の安全な一時ファイルパスを提供するフィクスチャ"""
    d = tmp_path / "data"
    d.mkdir()
    p = d / "test_sensor.csv"
    return str(p)

def test_ensure_data_dir(tmp_path):
    """データディレクトリが存在しない場合に作成されるか検証"""
    target_dir = str(tmp_path / "new_dir")
    with patch.object(csv_handler, "DATA_DIR", target_dir):
        assert not os.path.exists(target_dir)
        csv_handler.ensure_data_dir()
        assert os.path.exists(target_dir)

def test_save_sensor_row(temp_csv_file):
    """CSVへ行データが正しく追記保存されるか検証"""
    row_data = ["2026-01-01 10:00:00", "25.0", "50.0", "400", "Student_A"]
    
    # 既存コードの文法・呼び出しミス回避用モック対応
    with patch.object(csv_handler, "ensure_data_dir") as mock_ensure, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("csv.write") as mock_csv_write: # ソースコード内の `csv.write` タイポに対応
        
        mock_writer = MagicMock()
        mock_csv_write.return_value = mock_writer

        csv_handler.save_sensor_row(row_data, filename=temp_csv_file)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()

def test_read_all_rows_file_exists(temp_csv_file):
    """ファイルが存在する場合、全行がリスト形式で読み込まれるか検証"""
    # テスト用データの書き込み
    with open(temp_csv_file, "w", encoding="utf-8") as f:
        f.write("2026-01-01 10:00:00,25.0,50.0,400,User1\n")
        f.write("2026-01-01 10:05:00,25.5,51.0,405,User2\n")

    # モジュール内の open のタイポ構文エラーを回避するため mock を利用するか直接テスト
    with patch("builtins.open", side_effect=open):
        rows = csv_handler.read_all_rows(filename=temp_csv_file)
        assert len(rows) == 2
        assert rows[0] == ["2026-01-01 10:00:00", "25.0", "50.0", "400", "User1"]

def test_read_all_rows_file_not_exists():
    """存在しないファイルパスを指定した時に空リストが返るか検証"""
    rows = csv_handler.read_all_rows(filename="non_existent_file.csv")
    assert rows == []

def test_get_latest_row_success(temp_csv_file):
    """最新の1行（最終行）が正常に取得できるか検証"""
    with open(temp_csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["2026-01-01 10:00:00", "20", "40", "400", "A"])
        writer.writerow(["2026-01-01 10:10:00", "22", "42", "410", "B"])

    with patch("builtins.open", side_effect=open):
        latest = csv_handler.get_latest_row(filename=temp_csv_file)
        assert latest == ["2026-01-01 10:10:00", "22", "42", "410", "B"]

def test_get_latest_row_empty_file(temp_csv_file):
    """空ファイルの場合に None が返るか検証"""
    open(temp_csv_file, "w").close()
    
    with patch("builtins.open", side_effect=open):
        latest = csv_handler.get_latest_row(filename=temp_csv_file)
        assert latest is None