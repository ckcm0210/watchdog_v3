import pytest
import os
import sys

# 將專案根目錄添加到 sys.path，以解決模組匯入問題
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from utils.helpers import _baseline_key_for_path

def test_baseline_key_for_path_normal():
    """
    測試標準路徑是否能生成預期的 key。
    """
    path = r"C:\Users\user\Documents\My File.xlsx"
    key = _baseline_key_for_path(path)
    # 檢查檔名是否存在
    assert "My File.xlsx" in key
    # 檢查是否包含 hash 分隔符
    assert "__" in key
    # 檢查 hash 長度是否為 8
    assert len(key.split('__')[-1]) == 8

def test_baseline_key_for_path_long_filename():
    """
    測試超長檔名是否會被正確截斷。
    """
    long_name = "a" * 200 + ".xlsx"
    path = os.path.join("C:", "temp", long_name)
    key = _baseline_key_for_path(path)
    
    # 檔名部分應該被截斷，所以原始長檔名不應該完整出現在 key 中
    assert long_name not in key
    # 檢查截斷後的檔名部分是否仍然存在
    assert "a" * 140 in key # 140 is the MAX_BASE_NAME
    assert key.endswith(".xlsx__" + key.split('__')[-1])

def test_baseline_key_for_path_same_name_different_path():
    """
    測試相同檔名、不同路徑的檔案是否會生成不同的 key。
    """
    path1 = r"C:\folder1\data.xlsx"
    path2 = r"C:\folder2\data.xlsx"
    
    key1 = _baseline_key_for_path(path1)
    key2 = _baseline_key_for_path(path2)
    
    assert key1 != key2
    # 檔名部分應該相同
    assert key1.split('__')[0] == key2.split('__')[0]
    # Hash 部分應該不同
    assert key1.split('__')[1] != key2.split('__')[1]

def test_baseline_key_for_path_with_special_chars():
    """
    測試包含特殊字元的路徑。
    """
    path = r"C:\Users\user\Desktop\檔案 (新).xlsx"
    key = _baseline_key_for_path(path)
    assert "檔案 (新).xlsx" in key
    assert "__" in key

def test_baseline_key_for_path_removes_cache_prefix():
    """
    測試是否能正確移除快取產生的 hash 前綴。
    """
    # 模擬一個已經被快取過的檔名
    cached_name = "a1b2c3d4e5f6a1b2_My Report.xlsx"
    path = os.path.join("C:", "cache", cached_name)
    key = _baseline_key_for_path(path)
    
    # 原始的快取 hash 前綴不應該存在於 key 的檔名部分
    assert "a1b2c3d4e5f6a1b2_" not in key.split('__')[0]
    # 乾淨的檔名應該存在
    assert "My Report.xlsx" in key

if __name__ == "__main__":
    pytest.main()
