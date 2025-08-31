"""
系統配置設定
所有原始配置都在這裡，確保向後相容
"""
import os
from datetime import datetime

# =========== User Config ============
TRACK_EXTERNAL_REFERENCES = True       # 追蹤外部參照更新
TRACK_DIRECT_VALUE_CHANGES = True      # 追蹤直接值變更
TRACK_FORMULA_CHANGES = True           # 追蹤公式變更
IGNORE_INDIRECT_CHANGES = True         # 忽略間接影響
# 當外部參照公式的字串有改變，但實際數值（cached value）未變時，視為「無實質變更」
ENABLE_FORMULA_VALUE_CHECK = True
# 為了效能，只對前 N 個公式儲存格（跨所有表合計）查詢 cached value，超過則跳過值比對
MAX_FORMULA_VALUE_CELLS = 50000
ENABLE_BLACK_CONSOLE = True
CONSOLE_POPUP_ON_COMPARISON = True
CONSOLE_ALWAYS_ON_TOP = False           # 新增：是否始終置頂
CONSOLE_TEMP_TOPMOST_DURATION = 5       # 新增：臨時置頂持續時間（秒）
CONSOLE_INITIAL_TOPMOST_DURATION = 2    # 新增：初始置頂持續時間（秒）
SHOW_COMPRESSION_STATS = False          # 關閉壓縮統計顯示
SHOW_DEBUG_MESSAGES = False             # 關閉調試訊息
AUTO_UPDATE_BASELINE_AFTER_COMPARE = True  # 比較後自動更新基準線
SCAN_ALL_MODE = True
# 指定啟動掃描要建立基準線的子集資料夾（留空則使用 WATCH_FOLDERS 全部）
SCAN_TARGET_FOLDERS = []
MAX_CHANGES_TO_DISPLAY = 20 # 限制顯示的變更數量，0 表示不限制
USE_LOCAL_CACHE = True
CACHE_FOLDER = r"C:\Users\user\Desktop\watchdog\cache_folder"
# 嚴格模式：永不開原檔（copy 失敗則跳過處理）
STRICT_NO_ORIGINAL_READ = True
# 複製重試次數與退避（秒）
COPY_RETRY_COUNT = 10
COPY_RETRY_BACKOFF_SEC = 1.0
# （可選）分塊複製的塊大小（MB），0 表示不用分塊特別處理
COPY_CHUNK_SIZE_MB = 4
# 複製完成後的短暫等待（秒），給檔案系統穩定
COPY_POST_SLEEP_SEC = 0.2
# 複製前穩定性預檢：連續 N 次 mtime 不變才開始複製
COPY_STABILITY_CHECKS = 5
COPY_STABILITY_INTERVAL_SEC = 1.0
COPY_STABILITY_MAX_WAIT_SEC = 12.0
ENABLE_FAST_MODE = True
# Phase 1 new controls
QUICK_SKIP_BY_STAT = True           # 若 mtime/size 與基準線一致則直接跳過讀取
MTIME_TOLERANCE_SEC = 2.0           # mtime 容差（秒）
POLLING_STABLE_CHECKS = 3           # 輪巡：連續多少次「無變化」才算穩定
POLLING_COOLDOWN_SEC = 20           # 每檔案成功比較後的冷靜期（秒）
SKIP_WHEN_TEMP_LOCK_PRESENT = True  # 偵測到 ~$ 鎖檔時延後觸碰
# Phase 2: 複製引擎選擇
COPY_ENGINE = 'python'              # 'python' | 'powershell' | 'robocopy'
PREFER_SUBPROCESS_FOR_XLSM = True   # 對 .xlsm 檔優先使用子程序複製
SUBPROCESS_ENGINE_FOR_XLSM = 'robocopy'  # 'powershell' | 'robocopy'
ENABLE_TIMEOUT = True
FILE_TIMEOUT_SECONDS = 120
ENABLE_MEMORY_MONITOR = True
MEMORY_LIMIT_MB = 2048
ENABLE_RESUME = True
FORMULA_ONLY_MODE = True
DEBOUNCE_INTERVAL_SEC = 4

# =========== Compression Config ============
# 預設壓縮格式：'lz4' 用於頻繁讀寫, 'zstd' 用於長期存儲, 'gzip' 用於兼容性
DEFAULT_COMPRESSION_FORMAT = 'lz4'  # 'lz4', 'zstd', 'gzip'

# 壓縮級別設定
LZ4_COMPRESSION_LEVEL = 1       # LZ4: 0-16, 越高壓縮率越好但越慢
ZSTD_COMPRESSION_LEVEL = 3      # Zstd: 1-22, 推薦 3-6
GZIP_COMPRESSION_LEVEL = 6      # gzip: 1-9, 推薦 6

# 歸檔設定
ENABLE_ARCHIVE_MODE = True              # 是否啟用歸檔模式
ARCHIVE_AFTER_DAYS = 7                  # 多少天後轉為歸檔格式
ARCHIVE_COMPRESSION_FORMAT = 'zstd'     # 歸檔使用的壓縮格式

# 效能監控
SHOW_COMPRESSION_STATS = True           # 是否顯示壓縮統計

RESUME_LOG_FILE = r"C:\Users\user\Desktop\watchdog\resume_log\baseline_progress.log"
WATCH_FOLDERS = [
    r"C:\Users\user\Desktop\Test",
]
MANUAL_BASELINE_TARGET = []
LOG_FOLDER = r"C:\Users\user\Desktop\watchdog\log_folder"
LOG_FILE_DATE = datetime.now().strftime('%Y%m%d')
CSV_LOG_FILE = os.path.join(LOG_FOLDER, f"excel_change_log_{LOG_FILE_DATE}.csv.gz")
# Console 純文字日誌
CONSOLE_TEXT_LOG_ENABLED = True
CONSOLE_TEXT_LOG_FILE = os.path.join(LOG_FOLDER, f"console_log_{LOG_FILE_DATE}.txt")
# 只將「變更相關」訊息寫入文字檔（比較表格、變更橫幅）
CONSOLE_TEXT_LOG_ONLY_CHANGES = True
SUPPORTED_EXTS = ('.xlsx', '.xlsm')
# 只監控變更但不預先建立 baseline 的資料夾（例如整個磁碟機根目錄）。
# 在這些路徑內，首次偵測到變更會先記錄資訊並建立 baseline，之後才進入正常比較流程。
MONITOR_ONLY_FOLDERS = []
# 監控資料夾中的排除清單（子資料夾）。位於此清單的路徑不做即時比較。
WATCH_EXCLUDE_FOLDERS = []
# 只監控變更根目錄中的排除清單（子資料夾）。位於此清單的路徑不做 monitor-only。
MONITOR_ONLY_EXCLUDE_FOLDERS = []
# 忽略 CACHE_FOLDER 下的所有事件
IGNORE_CACHE_FOLDER = True
IGNORE_LOG_FOLDER = True            # 忽略 LOG_FOLDER 內的所有事件（避免自我觸發）
ENABLE_OPS_LOG = True               # 啟用 ops 複製成功/失敗 CSV 記錄
MAX_RETRY = 10
RETRY_INTERVAL_SEC = 2
USE_TEMP_COPY = True
WHITELIST_USERS = ['ckcm0210', 'yourwhiteuser']
LOG_WHITELIST_USER_CHANGE = True
# CSV 記錄去重時間窗（秒）：相同內容在此時間窗內不重複記錄
LOG_DEDUP_WINDOW_SEC = 300
FORCE_BASELINE_ON_FIRST_SEEN = [
    r"\\network_drive\\your_folder1\\must_first_baseline.xlsx",
    "force_this_file.xlsx"
]

# =========== Polling Config ============
POLLING_SIZE_THRESHOLD_MB = 10

# =========== Console 比較表格顯示 ============
# Address 欄寬（字元，0=自動依目前變更的最長 Address）
ADDRESS_COL_WIDTH = 0
# 覆蓋比較表格的總寬度（字元，0=自動偵測終端寬度或使用 120）
CONSOLE_TERM_WIDTH_OVERRIDE = 0
# 將標頭的時間/作者資訊改到下一行顯示（讓 Baseline/Current 標頭更短，內容空間更寬）
HEADER_INFO_SECOND_LINE = True
# 內容差異高亮顯示（以 «…» 標示差異區段）
DIFF_HIGHLIGHT_ENABLED = True
DENSE_POLLING_INTERVAL_SEC = 10
DENSE_POLLING_DURATION_SEC = 15
SPARSE_POLLING_INTERVAL_SEC = 60
SPARSE_POLLING_DURATION_SEC = 15

# =========== 值/公式讀取引擎（高效） ============
# 值讀取引擎：'polars'（預設，需安裝 polars/xlsx2csv）或 'xml'（純 XML 直讀）
VALUE_ENGINE = 'polars_xml'
# CSV 是否落地保存（polars 模式下除錯用；預設 False，使用 BytesIO in-memory）
CSV_PERSIST = True  # 預設開啟（合併 CSV：<CACHE_FOLDER>/values/<baseline_key>.values.csv）
# 公式讀取引擎：暫保留 openpyxl；之後可提供 'xml'
FORMULA_ENGINE = 'openpyxl'
# 允許的最大並發 sheet 讀取數
MAX_SHEET_WORKERS = 4

# =========== 歷史快照與時間線（Git/SQLite） ============
ENABLE_HISTORY_SNAPSHOT = True
HISTORY_GIT_REPO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'excel_git_repo')
HISTORY_SYNC_FULL = True
HISTORY_SYNC_SUMMARY = True
HISTORY_GIT_AUTHOR_FROM_EXCEL = True
EVENTS_SQLITE_PATH = os.path.join(LOG_FOLDER, 'events.sqlite')

# Timeline UI defaults (for /ui/timeline)
UI_TIMELINE_DEFAULT_DAYS = 7                 # 預設顯示最近幾天
UI_TIMELINE_PAGE_SIZE = 50                   # 預設每頁 50 筆
UI_TIMELINE_MAX_PAGE_SIZE = 200              # 上限 200
UI_TIMELINE_WARN_DAYS = 180                  # 超過 180 天提示
UI_TIMELINE_GROUP_BY_BASEKEY = False         # 是否按檔案分組（可於 UI 切換）
UI_TIMELINE_DEFAULT_HAS_SNAPSHOT = 'yes'     # 'ignore' | 'yes' | 'no'
UI_TIMELINE_DEFAULT_HAS_SUMMARY = 'ignore'   # 'ignore' | 'yes' | 'no'
UI_TIMELINE_DEFAULT_MIN_TOTAL = 1            # 預設最小 total_changes 門檻
UI_TIMELINE_DEFAULT_SORT = 'desc'            # 'desc' | 'asc'

# 路徑映射（跨機器路徑差異）：每行一個規則，示例：\\\servername\share => D:\shared
PATH_MAPPINGS = []

# 內嵌 Timeline 伺服器（融入 watchdog 主程式）
ENABLE_TIMELINE_SERVER = True
TIMELINE_SERVER_HOST = '127.0.0.1'
TIMELINE_SERVER_PORT = 5000
OPEN_TIMELINE_ON_START = True

# =========== 比較與外部參照行為 ============
SHOW_EXTERNAL_REFRESH_CHANGES = True                 # 公式不變但外部 refresh 令結果變，是否顯示
SUPPRESS_INTERNAL_FORMULA_CHANGE_WITH_SAME_VALUE = False  # 內部公式改變但結果相同時，是否抑制顯示
ALWAYS_SHOW_EXTERNAL_REFRESH_UPDATE_WHEN_FORMULA_ONLY = True  # 即使 FORMULA_ONLY_MODE=True 也顯示外部 refresh

# =========== 輸出清潔 ============
REMOVE_EMOJI = True  # 移除 console/日誌輸出中的 emoji

# =========== 全局變數 ============
current_processing_file = None
processing_start_time = None
force_stop = False
baseline_completed = False