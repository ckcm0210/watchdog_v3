# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, abort, request, redirect
try:
    import git
except Exception as e:
    git = None
import os
from datetime import datetime
import webbrowser
import json

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# 初始化和設定
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
app = Flask(__name__)
REPO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'excel_git_repo')

# --- Timeline imports ---
try:
    from utils.events_db import query_events, get_event_by_id, get_neighbor_event
    from utils.compression import load_compressed_file
    import config.settings as settings
    from utils.helpers import map_path_for_display, human_readable_size
    HAS_TIMELINE = True
except Exception as _e:
    HAS_TIMELINE = False
    settings = None

# 檢查 Git 倉庫是否存在
if git is None:
    print("錯誤：未安裝 GitPython（套件名 GitPython）。請先 pip install GitPython 後重試。")
    repo = None
else:
    try:
        repo = git.Repo(REPO_PATH)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        print(f"錯誤：在 '{REPO_PATH}' 中找不到有效的 Git 倉庫。")
        print("請先在該資料夾初始化：git init；並把想追蹤的檔案 commit 進去。")
        repo = None

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# HTML 模板
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel 檔案歷史查看器</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #0056b3; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
        .file-list { list-style-type: none; padding: 0; }
        .file-list li { margin-bottom: 10px; }
        .file-list a { text-decoration: none; color: #007bff; font-weight: bold; font-size: 1.1em; }
        .file-list a:hover { text-decoration: underline; }
        .commit-history { margin-top: 30px; }
        .commit { border: 1px solid #e9ecef; padding: 15px; margin-bottom: 15px; border-radius: 6px; background-color: #fff; }
        .commit-meta { font-size: 0.9em; color: #6c757d; margin-bottom: 10px; }
        .commit-meta strong { color: #495057; }
        .commit-message { font-size: 1.05em; margin-bottom: 0; }
        .breadcrumb { margin-bottom: 20px; font-size: 1.1em; }
        .breadcrumb a { color: #007bff; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .error { color: #dc3545; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        {% if error %}
            <h1>錯誤</h1>
            <div class="error">{{ error }}</div>
        {% elif commit_pairs is defined %}
            <div class="breadcrumb"><a href="/">返回檔案列表</a></div>
            <h1>變更歷史</h1>
            <h2>檔案: {{ file_path }}</h2>
            <div class="commit-history">
                {% if commit_pairs %}
                    <form method="get" action="/diff">
                        <input type="hidden" name="file" value="{{ file_path }}">
                        <label>選擇版本 A：</label>
                        <select name="a">
                            {% for c in commit_pairs %}
                                <option value="{{ c.hexsha }}">{{ c.hexsha[:10] }} - {{ c.committed_datetime.strftime('%Y-%m-%d %H:%M:%S') }}</option>
                            {% endfor %}
                        </select>
                        <label>版本 B：</label>
                        <select name="b">
                            {% for c in commit_pairs %}
                                <option value="{{ c.hexsha }}">{{ c.hexsha[:10] }} - {{ c.committed_datetime.strftime('%Y-%m-%d %H:%M:%S') }}</option>
                            {% endfor %}
                        </select>
                        <label><input type="checkbox" name="meaningful" value="1" checked> 只顯示有意義變更</label>
                        <button type="submit">比較這兩個版本</button>
                    </form>
                    <hr>
                    {% for c in commit_pairs %}
                    <div class="commit">
                        <div class="commit-meta">
                            <strong>Commit:</strong> {{ c.hexsha[:10] }} | 
                            <strong>作者:</strong> {{ c.author.name }} &lt;{{ c.author.email }}&gt; | 
                            <strong>日期:</strong> {{ c.committed_datetime.strftime('%Y-%m-%d %H:%M:%S') }}
                        </div>
                        <p class="commit-message">{{ c.message | replace('\n', '<br>') | safe }}</p>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>找不到此檔案的任何提交歷史。</p>
                {% endif %}
            </div>
        {% else %}
            <h1>Excel 檔案歷史倉庫</h1>
            <h2>請選擇一個檔案查看其變更歷史：</h2>
            <ul class="file-list">
                {% for file in files %}
                <li><a href="/history/{{ file }}">{{ file }}</a></li>
                {% else %}
                <li>倉庫中沒有找到任何檔案。</li>
                {% endfor %}
            </ul>
        {% endif %}
    </div>
</body>
</html>
"""

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# Flask 路由
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

@app.route('/ui/timeline')
def ui_timeline():
    if not HAS_TIMELINE:
        return render_template_string(HTML_TEMPLATE, error='Timeline 模組未初始化')
    # 讀取查詢參數與預設
    from_dt = request.args.get('from')
    to_dt = request.args.get('to')
    base_key = request.args.get('base_key')
    q = request.args.get('q')
    author = request.args.get('author')
    types = request.args.get('types')
    min_total = request.args.get('min_total')
    has_snapshot = request.args.get('has_snapshot')
    has_summary = request.args.get('has_summary')
    sort = (request.args.get('sort') or settings.UI_TIMELINE_DEFAULT_SORT).upper()
    page = int(request.args.get('page') or 1)
    limit = int(request.args.get('limit') or settings.UI_TIMELINE_PAGE_SIZE)
    group = request.args.get('group')
    page_size_options = [25, 50, 100, 200]
    if limit not in page_size_options:
        page_size_options.append(limit)
        page_size_options = sorted(set(page_size_options))
    # tri-state 解析
    def _tri(v, default='ignore'):
        if v is None: v = default
        v = str(v).lower()
        if v in ('1','true','yes','y','on','t','是','有','yes','true'): return True
        if v in ('0','false','no','n','off','f','否','無'): return False
        return None
    hs = _tri(has_snapshot, settings.UI_TIMELINE_DEFAULT_HAS_SNAPSHOT)
    hsum = _tri(has_summary, settings.UI_TIMELINE_DEFAULT_HAS_SUMMARY)
    # types 列表
    type_list = [t.strip() for t in (types or '').split(',') if t.strip()]
    # 日期預設（最近 N 天）
    from datetime import datetime, timedelta
    if not from_dt and settings.UI_TIMELINE_DEFAULT_DAYS:
        from_dt = (datetime.now() - timedelta(days=int(settings.UI_TIMELINE_DEFAULT_DAYS))).isoformat(timespec='seconds')
    filters = {
        'base_key': base_key,
        'q': q,
        'author': author,
        'from': from_dt,
        'to': to_dt,
        'types': type_list,
        'min_total': int(min_total) if (min_total or '').strip().isdigit() else settings.UI_TIMELINE_DEFAULT_MIN_TOTAL,
        'has_snapshot': hs,
        'has_summary': hsum,
    }
    # 查詢
    data = query_events(filters=filters, page=page, limit=limit, sort=sort, count_total=True, aggregates=True, top_authors=3,
                        db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
    # 濾器 UI（表單）
    def _opt(selected, value):
        return ' selected' if str(selected) == str(value) else ''
    def _checked(name):
        return 'checked' if name in set(t.lower() for t in type_list) else ''
    def _tri_val(v):
        if v is True: return 'yes'
        if v is False: return 'no'
        return 'ignore'
    # Summary bar & Top authors
    sums = data.get('sums') or {}
    top = data.get('top_authors') or []
    def _badge(label, val):
        if val and int(val) > 0:
            return f'<span class="chip">{label}: {int(val)}</span>'
        return ''
    # 組裝 HTML
    html = [
        """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; background:#f5f6f8; color:#333; }
            .wrap { max-width: 1060px; margin: 18px auto; background:#fff; padding:18px 22px; border-radius:10px; box-shadow:0 2px 10px rgba(0,0,0,.06); }
            h1 { margin:0 0 8px; color:#0b5cab; }
            form.filters { display:flex; flex-wrap:wrap; gap:12px 16px; align-items:flex-end; margin:10px 0 14px; }
            .field { display:flex; flex-direction:column; min-width:180px; }
            .field label { font-size:12px; color:#666; margin-bottom:4px; }
            input[type=text], select { padding:6px 8px; border:1px solid #ccc; border-radius:6px; min-width:180px; }
            .actions { margin-left:auto; display:flex; gap:8px; }
            .btn { padding:6px 10px; background:#0b5cab; color:#fff; text-decoration:none; border-radius:6px; border:0; cursor:pointer; }
            .btn.secondary { background:#6c757d; }
            .summary { background:#f7fbff; border:1px solid #e1eefc; border-radius:8px; padding:10px; margin:10px 0; }
            .chips { margin-top:6px; }
            .chip { display:inline-block; background:#eef5ff; border:1px solid #d9e7ff; padding:2px 8px; border-radius:999px; margin-right:6px; font-size:12px; }
            .authors .chip { background:#f1f3f5; border-color:#e9ecef; }
            details.group { border:1px solid #eee; border-radius:8px; margin:10px 0; padding:6px 10px; }
            details.group summary { cursor:pointer; font-weight:600; }
            ul.events { list-style:none; padding-left:16px; }
            ul.events li { margin:6px 0; }
            .muted { color:#777; }
            .footer { margin-top:10px; font-size:12px; color:#666; }
        </style>
        """,
        "<div class='wrap'>",
        "<h1>Timeline</h1>",
        "<form class='filters' method='get'>",
        f"<div class='field'><label>Search file/base_key</label><input type='text' name='q' value='{q or ''}' placeholder='keyword or path'></div>",
        f"<div class='field'><label>Base key</label><input type='text' name='base_key' value='{base_key or ''}' placeholder='exact base_key'></div>",
        f"<div class='field'><label>Author</label><input type='text' name='author' value='{author or ''}' placeholder='name'></div>",
        f"<div class='field'><label>From (ISO)</label><input type='text' name='from' value='{from_dt or ''}' placeholder='YYYY-MM-DDTHH:MM:SS'></div>",
        f"<div class='field'><label>To (ISO)</label><input type='text' name='to' value='{to_dt or ''}' placeholder='YYYY-MM-DDTHH:MM:SS'></div>",
        f"<div class='field'><label>Has snapshot</label><select name='has_snapshot'>"
          f"<option value='ignore'{_opt(_tri_val(hs),'ignore')}>忽略</option>"
          f"<option value='yes'{_opt(_tri_val(hs),'yes')}>只要</option>"
          f"<option value='no'{_opt(_tri_val(hs),'no')}>不要</option>"
        "</select></div>",
        f"<div class='field'><label>Has summary</label><select name='has_summary'>"
          f"<option value='ignore'{_opt(_tri_val(hsum),'ignore')}>忽略</option>"
          f"<option value='yes'{_opt(_tri_val(hsum),'yes')}>只要</option>"
          f"<option value='no'{_opt(_tri_val(hsum),'no')}>不要</option>"
        "</select></div>",
        f"<div class='field'><label>Types</label>"
          f"<label><input type='checkbox' name='t_dvc' value='dvc' {_checked('dvc')}> DVC</label>"
          f"<label><input type='checkbox' name='t_fci' value='fci' {_checked('fci')}> FCI</label>"
          f"<label><input type='checkbox' name='t_xrlc' value='xrlc' {_checked('xrlc')}> XRLC</label>"
          f"<label><input type='checkbox' name='t_xru' value='xru' {_checked('xru')}> XRU</label>"
          f"<label><input type='checkbox' name='t_addc' value='addc' {_checked('addc')}> ADD</label>"
          f"<label><input type='checkbox' name='t_delc' value='delc' {_checked('delc')}> DEL</label>"
        "</div>",
        f"<div class='field'><label>Min total changes</label><input type='text' name='min_total' value='{min_total or settings.UI_TIMELINE_DEFAULT_MIN_TOTAL}'></div>",
        f"<div class='field'><label>Sort</label><select name='sort'>"
          f"<option value='desc'{_opt(sort,'DESC')}>Newest first</option>"
          f"<option value='asc'{_opt(sort,'ASC')}>Oldest first</option>"
        "</select></div>",
        f"<div class='field'><label>Page size</label><select name='limit'>"
          + ''.join([f"<option value='{n}'{_opt(limit,n)}>{n}</option>" for n in page_size_options]) +
        "</select></div>",
        f"<div class='field'><label>Grouping</label><select name='group'>"
          f"<option value='0'{_opt(group or ('1' if getattr(settings,'UI_TIMELINE_GROUP_BY_BASEKEY', False) else '0'),'0')}>不分組</option>"
          f"<option value='1'{_opt(group or ('1' if getattr(settings,'UI_TIMELINE_GROUP_BY_BASEKEY', False) else '0'),'1')}>按 base_key 分組</option>"
        "</select></div>",
        "<div class='actions'>",
        "  <button type='submit' class='btn'>Apply</button>",
        "  <a class='btn secondary' href='/ui/timeline'>Reset</a>",
        "</div>",
        # 隱藏字段：合成 types
        f"<input type='hidden' name='types' value='{','.join(type_list)}'>",
        "</form>",
    ]
    # 快捷日期 preset
    html.append("<div class='muted'>Presets: ")
    import urllib.parse as _uq
    def _preset(days):
        frm = (datetime.now() - timedelta(days=days)).isoformat(timespec='seconds')
        qs = {
            'from': frm,
            'to': '',
            'q': q or '', 'base_key': base_key or '', 'author': author or '',
            'types': ','.join(type_list), 'has_snapshot': _tri_val(hs), 'has_summary': _tri_val(hsum),
            'min_total': filters['min_total'], 'sort': sort, 'limit': limit, 'group': group or ''
        }
        return f"<a href='/ui/timeline?{_uq.urlencode(qs)}'>{days}d</a>"
    html.append(' | '.join([_preset(1), _preset(7), _preset(14), _preset(30)]))
    html.append("</div>")
    # Summary
    html.append("<div class='summary'>")
    html.append(f"<div>總事件: {data.get('total') or 0} ｜ 檔案數: {sums.get('files') or 0}</div>")
    html.append("<div class='chips'>" + ''.join([
        _badge('TOTAL', sums.get('total_changes', 0)),
        _badge('DVC', sums.get('dvc', 0)),
        _badge('FCI', sums.get('fci', 0)),
        _badge('XRLC', sums.get('xrlc', 0)),
        _badge('XRU', sums.get('xru', 0)),
        _badge('ADD', sums.get('addc', 0)),
        _badge('DEL', sums.get('delc', 0)),
    ]) + "</div>")
    if top:
        html.append("<div class='authors'><span class='muted'>Top authors:</span> " + ' '.join([f"<span class='chip'>{t['last_author'] or 'Unknown'}: {t['count']}</span>" for t in top]) + "</div>")
    html.append("</div>")
    # 列表或分組
    items = data.get('items') or []
    do_group = (group or ('1' if getattr(settings,'UI_TIMELINE_GROUP_BY_BASEKEY', False) else '0')) == '1'
    if do_group:
        groups = {}
        for it in items:
            groups.setdefault(it.get('base_key'), []).append(it)
        for bk, rows in groups.items():
            cnt = len(rows)
            first = rows[0]
            fn = os.path.basename(first.get('file_path') or '')
            html.append(f"<details class='group'><summary>{bk} • {fn} <span class='muted'>({cnt} events)</span></summary>")
            html.append('<ul class="events">')
            for it in rows:
                fn = os.path.basename(it.get('file_path') or '')
                t = it.get('event_time')
                size = human_readable_size(it.get('source_size'))
                author = it.get('last_author') or 'Unknown'
                counters = ' '.join([
                    _badge('Δ', it.get('total_changes')),
                    _badge('DVC', it.get('dvc')),
                    _badge('FCI', it.get('fci')),
                    _badge('XRLC', it.get('xrlc')),
                    _badge('XRU', it.get('xru')),
                    _badge('ADD', it.get('addc')),
                    _badge('DEL', it.get('delc')),
                ])
                html.append(f"<li>[{t}] {fn} | {author} • {size} | "
                            f"<a href='/ui/timeline/event/{it.get('id')}'>snapshot</a> | "
                            f"<a href='/ui/timeline/diff/{it.get('id')}?compare=prev&meaningful=1'>diff</a> | {counters}</li>")
            html.append('</ul></details>')
    else:
        html.append('<ul class="events">')
        for it in items:
            fn = os.path.basename(it.get('file_path') or '')
            bk = it.get('base_key')
            t = it.get('event_time')
            size = human_readable_size(it.get('source_size'))
            author = it.get('last_author') or 'Unknown'
            counters = ' '.join([
                _badge('Δ', it.get('total_changes')),
                _badge('DVC', it.get('dvc')),
                _badge('FCI', it.get('fci')),
                _badge('XRLC', it.get('xrlc')),
                _badge('XRU', it.get('xru')),
                _badge('ADD', it.get('addc')),
                _badge('DEL', it.get('delc')),
            ])
            html.append(f"<li>[{t}] {fn} — {bk} | {author} • {size} | "
                        f"<a href='/ui/timeline/event/{it.get('id')}'>snapshot</a> | "
                        f"<a href='/ui/timeline/diff/{it.get('id')}?compare=prev&meaningful=1'>diff</a> | {counters}</li>")
        html.append('</ul>')
    # Pagination
    total = data.get('total') or 0
    start = (page-1)*limit + 1 if total>0 else 0
    end = min(page*limit, total)
    html.append(f"<div class='footer'>Showing {start}-{end} of {total} | "
                f"<a href='?page={max(1,page-1)}&limit={limit}'>Prev</a> | "
                f"<a href='?page={page+1}&limit={limit}'>Next</a></div>")
    html.append('</div>')
    return '\n'.join(html)


@app.route('/ui/timeline/event/<int:event_id>')
def ui_timeline_event(event_id: int):
    if not HAS_TIMELINE:
        return render_template_string(HTML_TEMPLATE, error='Timeline 模組未初始化')
    evt = get_event_by_id(event_id, db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
    if not evt:
        return render_template_string(HTML_TEMPLATE, error=f'找不到事件 {event_id}')
    # 直接渲染 JSON（MVP）
    import html
    body = [f"<h1>Event #{event_id}</h1>"]
    body.append('<pre style="white-space:pre-wrap;">')
    for k in sorted(evt.keys()):
        v = evt[k]
        body.append(f"{html.escape(str(k))}: {html.escape(str(v))}")
    body.append('</pre>')
    # snapshot/summary 連結
    sp = evt.get('snapshot_path')
    if sp:
        body.append(f"<div>Snapshot: {html.escape(sp)}</div>")
    sm = evt.get('summary_path')
    if sm:
        body.append(f"<div>Summary: {html.escape(sm)}</div>")
    return '\n'.join(body)


@app.route('/ui/timeline/diff/<int:event_id>')
def ui_timeline_diff(event_id: int):
    if not HAS_TIMELINE:
        return render_template_string(HTML_TEMPLATE, error='Timeline 模組未初始化')
    import html
    evt = get_event_by_id(event_id, db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
    if not evt:
        return render_template_string(HTML_TEMPLATE, error=f'找不到事件 {event_id}')
    compare = request.args.get('compare','prev')
    meaningful = request.args.get('meaningful','1') == '1'
    # 找前後事件
    prev_evt = next_evt = None
    if compare == 'prev':
        prev_evt = get_neighbor_event(evt['base_key'], evt['event_time'], before=True, db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
    elif compare == 'next':
        next_evt = get_neighbor_event(evt['base_key'], evt['event_time'], before=False, db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
    elif compare.startswith('id:'):
        try:
            other_id = int(compare.split(':',1)[1])
            next_evt = get_event_by_id(other_id, db_path=getattr(settings, 'EVENTS_SQLITE_PATH', None))
        except Exception:
            pass
    # 讀 snapshot 檔
    def read_snapshot(path):
        try:
            # 去除副檔名再交給 load（會自動探測）
            for ext in ('.gz','.lz4','.zst'):
                if path.endswith(ext):
                    path = path[:-len(ext)]
                    break
            return load_compressed_file(path)
        except Exception:
            return None
    cur_snap = read_snapshot(evt.get('snapshot_path') or '')
    if prev_evt is not None:
        other_snap = read_snapshot(prev_evt.get('snapshot_path') or '')
    else:
        other_snap = read_snapshot(next_evt.get('snapshot_path') or '') if next_evt is not None else None
    if not cur_snap or not other_snap:
        return render_template_string(HTML_TEMPLATE, error='缺少快照，無法比較')
    # 計算簡單差異（沿用 git_viewer diff 概念）
    def _disp(x):
        if isinstance(x, dict):
            v = x.get('cached_value') if x.get('cached_value') is not None else x.get('value')
            f = x.get('formula')
            return v, f
        return x, None
    changes = []
    try:
        sheets = set((cur_snap.get('cells') or {}).keys()) | set((other_snap.get('cells') or {}).keys())
        for s in sorted(sheets):
            a_cells = (cur_snap.get('cells') or {}) if isinstance(cur_snap.get('cells'), dict) else cur_snap
            b_cells = (other_snap.get('cells') or {}) if isinstance(other_snap.get('cells'), dict) else other_snap
            a_ws = a_cells.get(s, {}) if isinstance(a_cells, dict) else {}
            b_ws = b_cells.get(s, {}) if isinstance(b_cells, dict) else {}
            addrs = set(a_ws.keys()) | set(b_ws.keys())
            for addr in sorted(addrs):
                av, af = _disp(a_ws.get(addr, {}))
                bv, bf = _disp(b_ws.get(addr, {}))
                if av == bv and af == bf:
                    continue
                ctype = 'MOD'
                if a_ws.get(addr) and not b_ws.get(addr):
                    ctype = 'DEL'
                elif not a_ws.get(addr) and b_ws.get(addr):
                    ctype = 'ADD'
                else:
                    if af != bf:
                        ctype = 'FORMULA'
                    elif av != bv:
                        ctype = 'VALUE'
                changes.append({'sheet': s, 'address': addr, 'type': ctype, 'old_value': av, 'new_value': bv, 'old_formula': af, 'new_formula': bf})
    except Exception:
        pass
    # 摘要
    summary = {'total': len(changes), 'by_type': {}}
    for c in changes:
        summary['by_type'][c['type']] = summary['by_type'].get(c['type'], 0) + 1
    # 輸出
    out = [f"<h1>Diff #{event_id}</h1>"]
    out.append(f"<p>總變更: {summary['total']} | 分類: {summary['by_type']}</p>")
    out.append('<table border="1" cellpadding="6" cellspacing="0"><tr><th>Sheet</th><th>Address</th><th>Type</th><th>Old</th><th>New</th><th>Old F</th><th>New F</th></tr>')
    for c in changes[:1000]:
        out.append(f"<tr><td>{c['sheet']}</td><td>{c['address']}</td><td>{c['type']}</td><td>{c['old_value']}</td><td>{c['new_value']}</td><td>{c['old_formula']}</td><td>{c['new_formula']}</td></tr>")
    out.append('</table>')
    return '\n'.join(out)

@app.route('/')
def index():
    # 主頁，顯示倉庫中的檔案列表。
    if not repo:
        return render_template_string(HTML_TEMPLATE, error=f"Git 倉庫 '{REPO_PATH}' 不存在或無效。")
    
    try:
        # 獲取最新一次提交中的所有檔案
        # 列出工作樹（工作目錄）中的檔案，若無提交亦可看到
        try:
            tree = repo.head.commit.tree
            files = [item.path for item in tree.traverse() if item.type == 'blob']
        except Exception:
            # 沒有提交時，從工作目錄掃描（限制在 repo.working_dir 底下）
            files = []
            root = repo.working_dir
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, root)
                    # 排除 .git 目錄
                    if rel.startswith('.git'+os.sep):
                        continue
                    files.append(rel)
        return render_template_string(HTML_TEMPLATE, files=files)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"無法讀取 Git 倉庫檔案列表: {e}")

@app.route('/history/<path:file_path>')
def history(file_path):
    # 顯示指定檔案的提交歷史。
    if not repo:
        return render_template_string(HTML_TEMPLATE, error=f"Git 倉庫 '{REPO_PATH}' 不存在或無效。")
    
    try:
        # 若沒有任何提交，直接顯示空
        if not repo.head.is_valid():
            return render_template_string(HTML_TEMPLATE, commit_pairs=[], file_path=file_path)
        # 僅顯示與該檔案有關的提交（最多 100 筆）
        commits = list(repo.iter_commits(paths=file_path, max_count=100))
        # 反序（最新在前）已是默認；若需只顯示前 N 可再切片
        # 若為 .xlsx 檔，嘗試引導至對應的 .cells.json
        if file_path.lower().endswith('.xlsx'):
            alt = file_path[:-5] + '.cells.json'
            # 只有當該 JSON 在任何提交中存在時才引導
            try:
                test = list(repo.iter_commits(paths=alt, max_count=1))
                if test:
                    return redirect(f"/history/{alt}")
            except Exception:
                pass
        return render_template_string(HTML_TEMPLATE, commit_pairs=commits, file_path=file_path)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f"無法獲取檔案 '{file_path}' 的歷史記錄: {e}")

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# Diff 視圖
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
@app.route('/diff')
def diff_view():
    if not repo:
        return render_template_string(HTML_TEMPLATE, error=f"Git 倉庫 '{REPO_PATH}' 不存在或無效。")
    file_path = request.args.get('file')
    sha_a = request.args.get('a')
    sha_b = request.args.get('b')
    only_meaningful = request.args.get('meaningful') == '1'
    if not file_path or not sha_a or not sha_b:
        return render_template_string(HTML_TEMPLATE, error='缺少必要參數 file/a/b')
    try:
        # 從指定的兩個 commit 讀取檔案內容（假設該檔案是 JSON）
        def _read_json_from_commit(sha):
            commit = repo.commit(sha)
            tree = commit.tree
            try:
                blob = tree / file_path
            except Exception:
                # 若路徑不存在於該次提交
                return {}
            data = blob.data_stream.read().decode('utf-8', 'ignore')
            try:
                return json.loads(data)
            except Exception:
                return {}
        ja = _read_json_from_commit(file_path if len(sha_a) == 0 else sha_a)
        jb = _read_json_from_commit(file_path if len(sha_b) == 0 else sha_b)
        # 計算差異（僅顯示有變化的地址）
        def _disp(x):
            if isinstance(x, dict):
                v = x.get('cached_value') if x.get('cached_value') is not None else x.get('value')
                f = x.get('formula')
                return v, f
            return x, None
        changes = []
        try:
            sheets = set((ja.get('cells') or {}).keys()) | set((jb.get('cells') or {}).keys())
            for s in sorted(sheets):
                a_cells = (ja.get('cells') or {}) if isinstance(ja.get('cells'), dict) else ja
                b_cells = (jb.get('cells') or {}) if isinstance(jb.get('cells'), dict) else jb
                a_ws = a_cells.get(s, {}) if isinstance(a_cells, dict) else {}
                b_ws = b_cells.get(s, {}) if isinstance(b_cells, dict) else {}
                addrs = set(a_ws.keys()) | set(b_ws.keys())
                for addr in sorted(addrs):
                    av, af = _disp(a_ws.get(addr, {}))
                    bv, bf = _disp(b_ws.get(addr, {}))
                    if av == bv and af == bf:
                        continue
                    # meaningful 過濾：只顯示直值變更/公式變更/新增/刪除
                    ctype = 'MOD'
                    if a_ws.get(addr) and not b_ws.get(addr):
                        ctype = 'DEL'
                    elif not a_ws.get(addr) and b_ws.get(addr):
                        ctype = 'ADD'
                    else:
                        if af != bf:
                            ctype = 'FORMULA'
                        elif av != bv:
                            ctype = 'VALUE'
                    if only_meaningful:
                        if ctype == 'MOD' and (af == bf):
                            # 純內部連鎖（值變但非外部 refresh）在這個 MVP 先不細分，保持顯示
                            pass
                    changes.append({'sheet': s, 'address': addr, 'type': ctype, 'old_value': av, 'new_value': bv, 'old_formula': af, 'new_formula': bf})
        except Exception:
            pass
        # 簡單摘要
        summary = {
            'total': len(changes),
            'by_type': {},
        }
        for c in changes:
            summary['by_type'][c['type']] = summary['by_type'].get(c['type'], 0) + 1
        # 以原模板呈現錯誤 or 在上面加一段摘要 + 簡列表
        table_html = '<h1>Diff 結果</h1>'
        table_html += f'<p>檔案: {file_path} | 版本 A: {sha_a[:10]} | 版本 B: {sha_b[:10]}</p>'
        table_html += f"<p>總變更: {summary['total']} | 分類: {summary['by_type']}</p>"
        table_html += '<table border="1" cellpadding="6" cellspacing="0"><tr><th>Sheet</th><th>Address</th><th>Type</th><th>Old</th><th>New</th><th>Old F</th><th>New F</th></tr>'
        for c in changes[:1000]:
            table_html += f"<tr><td>{c['sheet']}</td><td>{c['address']}</td><td>{c['type']}</td><td>{c['old_value']}</td><td>{c['new_value']}</td><td>{c['old_formula']}</td><td>{c['new_formula']}</td></tr>"
        table_html += '</table>'
        return table_html
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=f'無法計算差異: {e}')

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
# 主執行函數
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
def main():
    # 啟動 Flask 伺服器並打開瀏覽器。
    if not repo:
        # 如果倉庫無效，等待使用者按鍵後退出，避免視窗一閃而過
        input("Press Enter to exit...")
        return

    # 在啟動伺服器前先打開瀏覽器
    url = "http://127.0.0.1:5000"
    print(f" * 正在啟動 Git 歷史查看器...")
    print(f" * 請在瀏覽器中打開: {url}")
    webbrowser.open(url)
    
    # 啟動 Flask app
    # 使用 use_reloader=False 避免在 .bat 腳本中啟動兩次
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
