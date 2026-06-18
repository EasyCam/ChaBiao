"""FastAPI web interface for ChaBiao - browser-based spreadsheet viewer."""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

from .__version__ import __version__
from .core import SheetWorkbook, load_workbook


def create_app():
    """Create and configure the FastAPI application."""
    try:
        from fastapi import FastAPI, File, HTTPException, UploadFile
        from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
    except ImportError:
        raise ImportError("FastAPI dependencies required. Install with: pip install chabiao[web]")

    app = FastAPI(
        title="ChaBiao 查表",
        description="Fast spreadsheet viewer, filter and processor",
        version=__version__,
    )

    _workbooks: dict[str, SheetWorkbook] = {}

    @app.get("/")
    async def index():
        return HTMLResponse(_get_html_template())

    @app.post("/api/open")
    async def api_open(file: UploadFile = File(...), sheet: str | None = None):
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(file.filename).suffix
            ) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            wb = load_workbook(tmp_path, sheet_name=sheet if sheet else None)
            file_id = file.filename
            _workbooks[file_id] = wb
            info = wb.info_dict()
            return JSONResponse(
                {
                    "success": True,
                    "data": {
                        "file_id": file_id,
                        "sheets": wb.sheet_names,
                        "active_sheet": wb.active_sheet,
                        "info": info,
                    },
                }
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/sheets/{file_id}")
    async def api_sheets(file_id: str):
        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")
        return JSONResponse({"sheets": wb.sheet_names, "active": wb.active_sheet})

    @app.get("/api/data/{file_id}")
    async def api_data(
        file_id: str,
        sheet: str | None = None,
        start: int = 0,
        limit: int = 100,
        columns: str | None = None,
    ):
        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")
        df = wb.get_sheet(sheet)
        if columns:
            cols = [c.strip() for c in columns.split(",")]
            df = df[[c for c in cols if c in df.columns]]
        total = len(df)
        df_page = df.iloc[start : start + limit]
        return JSONResponse(
            {
                "total": total,
                "start": start,
                "limit": limit,
                "columns": list(df_page.columns),
                "rows": json.loads(df_page.to_json(orient="records", force_ascii=False)),
            }
        )

    @app.get("/api/filter/{file_id}")
    async def api_filter(
        file_id: str,
        column: str,
        contains: str | None = None,
        regex: str | None = None,
        equals: str | None = None,
        gt: float | None = None,
        lt: float | None = None,
        top_n: int | None = None,
        sheet: str | None = None,
    ):
        from .filters import auto_filter, filter_column

        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")

        if top_n:
            df = auto_filter(wb, column, top_n=top_n, sheet=sheet)
        else:
            df = filter_column(
                wb,
                column,
                contains=contains,
                regex=regex,
                equals=equals,
                greater_than=gt,
                less_than=lt,
                sheet=sheet,
            )

        return JSONResponse(
            {
                "total": len(df),
                "columns": list(df.columns),
                "rows": json.loads(df.to_json(orient="records", force_ascii=False)),
            }
        )

    @app.get("/api/search/{file_id}")
    async def api_search(
        file_id: str,
        keyword: str,
        columns: str | None = None,
        case_sensitive: bool = False,
        sheet: str | None = None,
    ):
        from .filters import search_keyword

        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")

        cols = [c.strip() for c in columns.split(",")] if columns else None
        df = search_keyword(wb, keyword, columns=cols, case_sensitive=case_sensitive, sheet=sheet)

        return JSONResponse(
            {
                "keyword": keyword,
                "total": len(df),
                "columns": list(df.columns),
                "rows": json.loads(df.to_json(orient="records", force_ascii=False)),
            }
        )

    @app.get("/api/columns/{file_id}")
    async def api_columns(file_id: str, sheet: str | None = None):
        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")
        columns = wb.columns(sheet)
        dtypes = wb.dtypes_info(sheet)
        unique_counts = {}
        for col in columns:
            try:
                unique_counts[col] = len(wb.unique_values(col, sheet=sheet))
            except Exception:
                unique_counts[col] = -1
        return JSONResponse(
            {
                "columns": columns,
                "dtypes": dtypes,
                "unique_counts": unique_counts,
            }
        )

    @app.get("/api/spotlight/{file_id}")
    async def api_spotlight(
        file_id: str,
        row: int,
        column: str | None = None,
        sheet: str | None = None,
    ):
        from .spotlight import spotlight as _spotlight
        from .spotlight import spotlight_cell

        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")

        if column:
            result = spotlight_cell(wb, row, column, sheet=sheet)
        else:
            result = _spotlight(wb, row, sheet=sheet)

        return JSONResponse({"success": True, "data": result})

    @app.get("/api/export/{file_id}")
    async def api_export(
        file_id: str,
        format: str = "csv",
        columns: str | None = None,
        sheet: str | None = None,
    ):
        wb = _workbooks.get(file_id)
        if not wb:
            raise HTTPException(status_code=404, detail="File not found")

        df = wb.get_sheet(sheet)
        if columns:
            cols = [c.strip() for c in columns.split(",")]
            df = df[[c for c in cols if c in df.columns]]

        buf = io.StringIO()
        if format == "csv":
            df.to_csv(buf, index=False)
            media_type = "text/csv"
            ext = "csv"
        elif format == "json":
            buf.write(df.to_json(orient="records", force_ascii=False))
            media_type = "application/json"
            ext = "json"
        else:
            buf_xlsx = io.BytesIO()
            df.to_excel(buf_xlsx, index=False)
            buf_xlsx.seek(0)
            return StreamingResponse(
                buf_xlsx,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=data.{ext}"},
            )

        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=data.{ext}"},
        )

    return app


def _get_html_template() -> str:
    return (
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChaBiao 查表 - Fast Spreadsheet Viewer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
.header { background: #1976D2; color: white; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }
.header h1 { font-size: 20px; font-weight: 600; }
.header .version { opacity: 0.8; font-size: 13px; }
.toolbar { background: white; padding: 12px 24px; border-bottom: 1px solid #e0e0e0; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.toolbar select, .toolbar input { padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
.toolbar input[type="text"] { flex: 1; min-width: 200px; }
.btn { padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-primary { background: #1976D2; color: white; }
.btn-primary:hover { background: #1565C0; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover { background: #d0d0d0; }
.info-bar { padding: 8px 24px; background: #E3F2FD; font-size: 13px; color: #1565C0; display: flex; justify-content: space-between; }
.container { padding: 16px 24px; }
.table-wrapper { overflow: auto; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-height: calc(100vh - 220px); }
table { width: 100%; border-collapse: collapse; }
th { position: sticky; top: 0; background: #1976D2; color: white; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 500; white-space: nowrap; z-index: 10; }
td { padding: 8px 14px; border-bottom: 1px solid #f0f0f0; font-size: 13px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
tr:hover td { background: #FFF8E1; }
tr.spotlight-row td { background: #FFF9C4 !important; }
td.spotlight-col { background: #FFF9C4 !important; }
td.spotlight-focus { background: #FFD600 !important; font-weight: 600; }
.pagination { display: flex; justify-content: center; gap: 8px; padding: 16px; }
.drop-zone { border: 2px dashed #ccc; border-radius: 8px; padding: 60px 20px; text-align: center; cursor: pointer; margin: 20px; background: white; }
.drop-zone:hover { border-color: #1976D2; background: #E3F2FD; }
.drop-zone h2 { color: #666; margin-bottom: 8px; }
.drop-zone p { color: #999; font-size: 14px; }
.loading { text-align: center; padding: 40px; font-size: 16px; color: #666; }
</style>
</head>
<body>
<div class="header">
  <h1>ChaBiao 查表 <span class="version">v"""
        + __version__
        + """</span></h1>
  <span class="version">Fast Spreadsheet Viewer / 闪电般的表格查阅筛选</span>
</div>
<div id="dropZone" class="drop-zone" ondrop="handleDrop(event)" ondragover="event.preventDefault()" onclick="document.getElementById('fileInput').click()">
  <h2>📁 Drop file here or click to open / 拖拽文件或点击打开</h2>
  <p>Supports .xlsx .xls .csv .tsv .xlsm files</p>
  <input type="file" id="fileInput" style="display:none" accept=".xlsx,.xls,.csv,.tsv,.xlsm" onchange="handleFile(this.files[0])">
</div>
<div id="toolbar" class="toolbar" style="display:none">
  <select id="sheetSelect" onchange="loadSheet(this.value)"></select>
  <select id="filterCol"></select>
  <select id="filterMode">
    <option value="contains">Contains 包含</option>
    <option value="equals">Equals 等于</option>
    <option value="regex">Regex 正则</option>
    <option value="search">Search all 搜索全部</option>
  </select>
  <input type="text" id="filterInput" placeholder="Filter keyword / 筛选关键词..." onkeydown="if(event.key==='Enter')doFilter()">
  <button class="btn btn-primary" onclick="doFilter()">Filter 筛选</button>
  <button class="btn btn-secondary" onclick="clearFilter()">Clear 清除</button>
  <label><input type="checkbox" id="spotlightToggle" onchange="toggleSpotlight()"> Spotlight 聚光灯</label>
</div>
<div id="infoBar" class="info-bar" style="display:none">
  <span id="fileInfo"></span>
  <span id="filterInfo"></span>
</div>
<div class="container">
  <div id="tableWrapper" class="table-wrapper" style="display:none">
    <table id="dataTable"><thead id="tableHead"></thead><tbody id="tableBody"></tbody></table>
  </div>
  <div id="pagination" class="pagination"></div>
</div>
<script>
let currentFileId = null;
let currentPage = 0;
let pageSize = 100;
let spotlightOn = false;
let spotlightRow = -1;
let spotlightCol = -1;

async function handleFile(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const resp = await fetch('/api/open', {method: 'POST', body: formData});
    const data = await resp.json();
    if (data.success) {
      currentFileId = data.data.file_id;
      document.getElementById('dropZone').style.display = 'none';
      document.getElementById('toolbar').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('tableWrapper').style.display = 'block';
      const sheetSelect = document.getElementById('sheetSelect');
      sheetSelect.innerHTML = '';
      data.data.sheets.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; sheetSelect.appendChild(o); });
      document.getElementById('fileInfo').textContent = `${data.data.file_id} | ${data.data.info.rows} rows × ${data.data.info.columns} cols`;
      await loadColumns();
      await loadData();
    }
  } catch(e) { alert('Error: ' + e.message); }
}

function handleDrop(e) {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  handleFile(file);
}

async function loadColumns() {
  const resp = await fetch(`/api/columns/${encodeURIComponent(currentFileId)}`);
  const data = await resp.json();
  const sel = document.getElementById('filterCol');
  sel.innerHTML = '';
  data.columns.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c + ` (${data.unique_counts[c]})`; sel.appendChild(o); });
}

async function loadData(start=0) {
  currentPage = start;
  const resp = await fetch(`/api/data/${encodeURIComponent(currentFileId)}?start=${start}&limit=${pageSize}`);
  const data = await resp.json();
  renderTable(data);
  renderPagination(data);
}

function renderTable(data) {
  const thead = document.getElementById('tableHead');
  const tbody = document.getElementById('tableBody');
  thead.innerHTML = '<tr>' + data.columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
  tbody.innerHTML = data.rows.map((row, i) =>
    '<tr onclick="onRowClick(' + i + ')" id="row-' + i + '">' +
    data.columns.map(c => `<td class="cell" data-col="${c}" data-row="${i}">${row[c] !== null && row[c] !== undefined ? row[c] : ''}</td>`).join('') +
    '</tr>'
  ).join('');
}

function renderPagination(data) {
  const total = data.total;
  const pages = Math.ceil(total / pageSize);
  const div = document.getElementById('pagination');
  if (pages <= 1) { div.innerHTML = ''; return; }
  let html = '';
  for (let i = 0; i < pages && i < 20; i++) {
    html += `<button class="btn ${i===currentPage?'btn-primary':'btn-secondary'}" onclick="loadData(${i*pageSize})">${i+1}</button>`;
  }
  if (pages > 20) html += `<span>... ${pages} pages</span>`;
  div.innerHTML = html;
}

async function doFilter() {
  const col = document.getElementById('filterCol').value;
  const keyword = document.getElementById('filterInput').value;
  const mode = document.getElementById('filterMode').value;
  let url;
  if (mode === 'search') {
    url = `/api/search/${encodeURIComponent(currentFileId)}?keyword=${encodeURIComponent(keyword)}`;
  } else if (mode === 'contains') {
    url = `/api/filter/${encodeURIComponent(currentFileId)}?column=${encodeURIComponent(col)}&contains=${encodeURIComponent(keyword)}`;
  } else if (mode === 'equals') {
    url = `/api/filter/${encodeURIComponent(currentFileId)}?column=${encodeURIComponent(col)}&equals=${encodeURIComponent(keyword)}`;
  } else {
    url = `/api/filter/${encodeURIComponent(currentFileId)}?column=${encodeURIComponent(col)}&regex=${encodeURIComponent(keyword)}`;
  }
  const resp = await fetch(url);
  const data = await resp.json();
  renderTable(data);
  document.getElementById('filterInfo').textContent = `Filter: ${data.total} results`;
}

async function clearFilter() {
  document.getElementById('filterInput').value = '';
  document.getElementById('filterInfo').textContent = '';
  await loadData();
}

function toggleSpotlight() {
  spotlightOn = document.getElementById('spotlightToggle').checked;
  if (!spotlightOn) clearSpotlight();
}

function onRowClick(rowIdx) {
  if (!spotlightOn) return;
  spotlightRow = rowIdx;
  applySpotlight();
}

function applySpotlight() {
  clearSpotlight();
  if (spotlightRow < 0) return;
  const rows = document.getElementById('tableBody').querySelectorAll('tr');
  rows.forEach((row, i) => {
    if (i === spotlightRow) {
      row.classList.add('spotlight-row');
      row.querySelectorAll('td').forEach(td => td.classList.add('spotlight-focus'));
    }
  });
}

function clearSpotlight() {
  document.querySelectorAll('.spotlight-row').forEach(r => r.classList.remove('spotlight-row'));
  document.querySelectorAll('.spotlight-focus').forEach(td => td.classList.remove('spotlight-focus'));
  document.querySelectorAll('.spotlight-col').forEach(td => td.classList.remove('spotlight-col'));
}

async function loadSheet(sheet) {
  await loadColumns();
  await loadData();
}
</script>
</body>
</html>"""
    )


def main(host: str = "0.0.0.0", port: int = 8900) -> None:
    """Run the ChaBiao web server."""
    try:
        import uvicorn
    except ImportError:
        raise ImportError("uvicorn required. Install with: pip install chabiao[web]")

    app = create_app()
    print(f"ChaBiao 查表 web interface starting at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
