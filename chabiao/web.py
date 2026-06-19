"""FastAPI web interface for ChaBiao — with i18n and dark theme support."""

from __future__ import annotations

import io
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .__version__ import __version__
from .core import SheetWorkbook, load_workbook
from .i18n import SUPPORTED_LANGS

_MAX_WORKERS = min(os.cpu_count() or 4, 8)

_WEB_STRINGS = {
    "en": {
        "title": "ChaBiao 查表 - Fast Spreadsheet Viewer",
        "subtitle": "Fast Spreadsheet Viewer / Lightning-fast table viewer",
        "drop_title": "📁 Drop file here or click to open",
        "drop_hint": "Supports .xlsx .xls .csv .tsv .xlsm files",
        "filter_placeholder": "Filter keyword...",
        "filter_btn": "Filter",
        "clear_btn": "Clear",
        "spotlight": "Spotlight",
        "filter_results": "Filter: {count} results",
        "loading": "Loading...",
        "error_open": "Error opening file",
        "contains": "Contains",
        "equals": "Equals",
        "regex": "Regex",
        "search_all": "Search all",
        "lang": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "rows_cols": "{rows} rows × {cols} cols",
    },
    "zh": {
        "title": "ChaBiao 查表 - 快速表格查看器",
        "subtitle": "闪电般的表格查阅筛选工具",
        "drop_title": "📁 拖拽文件到此处或点击打开",
        "drop_hint": "支持 .xlsx .xls .csv .tsv .xlsm 文件",
        "filter_placeholder": "筛选关键词...",
        "filter_btn": "筛选",
        "clear_btn": "清除",
        "spotlight": "聚光灯",
        "filter_results": "筛选: {count} 条结果",
        "loading": "加载中...",
        "error_open": "打开文件失败",
        "contains": "包含",
        "equals": "等于",
        "regex": "正则",
        "search_all": "搜索全部",
        "lang": "语言",
        "theme": "主题",
        "light": "亮色",
        "dark": "暗色",
        "rows_cols": "{rows} 行 × {cols} 列",
    },
    "ja": {
        "title": "ChaBiao 查表 - 高速スプレッドシートビューアー",
        "subtitle": "高速スプレッドシートビューアー",
        "drop_title": "📁 ファイルをドラッグ＆ドロップまたはクリックして開く",
        "drop_hint": ".xlsx .xls .csv .tsv .xlsm ファイル対応",
        "filter_placeholder": "フィルターキーワード...",
        "filter_btn": "フィルター",
        "clear_btn": "クリア",
        "spotlight": "スポットライト",
        "filter_results": "フィルター: {count} 件",
        "loading": "読み込み中...",
        "error_open": "ファイルを開けません",
        "contains": "含む",
        "equals": "等しい",
        "regex": "正規表現",
        "search_all": "全検索",
        "lang": "言語",
        "theme": "テーマ",
        "light": "ライト",
        "dark": "ダーク",
        "rows_cols": "{rows} 行 × {cols} 列",
    },
    "fr": {
        "title": "ChaBiao 查表 - Visionneuse de tableaux rapide",
        "subtitle": "Visionneuse de tableaux rapide",
        "drop_title": "📁 Déposez un fichier ici ou cliquez pour ouvrir",
        "drop_hint": "Supporte .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Mot-clé de filtre...",
        "filter_btn": "Filtrer",
        "clear_btn": "Effacer",
        "spotlight": "Projecteur",
        "filter_results": "Filtre : {count} résultats",
        "loading": "Chargement...",
        "error_open": "Erreur d'ouverture du fichier",
        "contains": "Contient",
        "equals": "Égal à",
        "regex": "Regex",
        "search_all": "Rechercher tout",
        "lang": "Langue",
        "theme": "Thème",
        "light": "Clair",
        "dark": "Sombre",
        "rows_cols": "{rows} lignes × {cols} colonnes",
    },
    "ru": {
        "title": "ChaBiao 查表 - Быстрый просмотр таблиц",
        "subtitle": "Быстрый просмотр и фильтрация таблиц",
        "drop_title": "📁 Перетащите файл или нажмите для открытия",
        "drop_hint": "Поддерживает .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Ключевое слово фильтра...",
        "filter_btn": "Фильтр",
        "clear_btn": "Очистить",
        "spotlight": "Прожектор",
        "filter_results": "Фильтр: {count} строк",
        "loading": "Загрузка...",
        "error_open": "Ошибка открытия файла",
        "contains": "Содержит",
        "equals": "Равно",
        "regex": "Рег. выражение",
        "search_all": "Искать везде",
        "lang": "Язык",
        "theme": "Тема",
        "light": "Светлая",
        "dark": "Тёмная",
        "rows_cols": "{rows} строк × {cols} столбцов",
    },
    "de": {
        "title": "ChaBiao 查表 - Schneller Tabellen-Betrachter",
        "subtitle": "Schneller Tabellen-Betrachter und Filter",
        "drop_title": "📁 Datei hierher ziehen oder klicken zum Öffnen",
        "drop_hint": "Unterstützt .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Filter-Schlüsselwort...",
        "filter_btn": "Filtern",
        "clear_btn": "Löschen",
        "spotlight": "Scheinwerfer",
        "filter_results": "Gefiltert: {count} Ergebnisse",
        "loading": "Laden...",
        "error_open": "Fehler beim Öffnen der Datei",
        "contains": "Enthält",
        "equals": "Gleich",
        "regex": "Regex",
        "search_all": "Alle suchen",
        "lang": "Sprache",
        "theme": "Design",
        "light": "Hell",
        "dark": "Dunkel",
        "rows_cols": "{rows} Zeilen × {cols} Spalten",
    },
    "es": {
        "title": "ChaBiao 查表 - Visor rápido de hojas de cálculo",
        "subtitle": "Visor rápido de hojas de cálculo",
        "drop_title": "📁 Arrastra un archivo aquí o haz clic para abrir",
        "drop_hint": "Soporta .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Palabra clave de filtro...",
        "filter_btn": "Filtrar",
        "clear_btn": "Limpiar",
        "spotlight": "Foco",
        "filter_results": "Filtro: {count} resultados",
        "loading": "Cargando...",
        "error_open": "Error al abrir el archivo",
        "contains": "Contiene",
        "equals": "Igual a",
        "regex": "Regex",
        "search_all": "Buscar todo",
        "lang": "Idioma",
        "theme": "Tema",
        "light": "Claro",
        "dark": "Oscuro",
        "rows_cols": "{rows} filas × {cols} columnas",
    },
    "pt": {
        "title": "ChaBiao 查表 - Visualizador rápido de planilhas",
        "subtitle": "Visualizador rápido de planilhas",
        "drop_title": "📁 Arraste um arquivo aqui ou clique para abrir",
        "drop_hint": "Suporta .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Palavra-chave do filtro...",
        "filter_btn": "Filtrar",
        "clear_btn": "Limpar",
        "spotlight": "Holofote",
        "filter_results": "Filtro: {count} resultados",
        "loading": "Carregando...",
        "error_open": "Erro ao abrir o arquivo",
        "contains": "Contém",
        "equals": "Igual a",
        "regex": "Regex",
        "search_all": "Pesquisar tudo",
        "lang": "Idioma",
        "theme": "Tema",
        "light": "Claro",
        "dark": "Escuro",
        "rows_cols": "{rows} linhas × {cols} colunas",
    },
    "it": {
        "title": "ChaBiao 查表 - Visualizzatore rapido di fogli",
        "subtitle": "Visualizzatore rapido di fogli di calcolo",
        "drop_title": "📁 Trascina un file qui o clicca per aprire",
        "drop_hint": "Supporta .xlsx .xls .csv .tsv .xlsm",
        "filter_placeholder": "Parola chiave filtro...",
        "filter_btn": "Filtra",
        "clear_btn": "Pulisci",
        "spotlight": "Riflettore",
        "filter_results": "Filtro: {count} risultati",
        "loading": "Caricamento...",
        "error_open": "Errore nell'aprire il file",
        "contains": "Contiene",
        "equals": "Uguale a",
        "regex": "Regex",
        "search_all": "Cerca tutto",
        "lang": "Lingua",
        "theme": "Tema",
        "light": "Chiaro",
        "dark": "Scuro",
        "rows_cols": "{rows} righe × {cols} colonne",
    },
    "ko": {
        "title": "ChaBiao 查表 - 빠른 스프레드시트 뷰어",
        "subtitle": "빠른 스프레드시트 뷰어 및 필터",
        "drop_title": "📁 파일을 드래그하거나 클릭하여 열기",
        "drop_hint": ".xlsx .xls .csv .tsv .xlsm 파일 지원",
        "filter_placeholder": "필터 키워드...",
        "filter_btn": "필터",
        "clear_btn": "지우기",
        "spotlight": "스포트라이트",
        "filter_results": "필터: {count}개 결과",
        "loading": "로딩 중...",
        "error_open": "파일 열기 오류",
        "contains": "포함",
        "equals": "같음",
        "regex": "정규식",
        "search_all": "전체 검색",
        "lang": "언어",
        "theme": "테마",
        "light": "라이트",
        "dark": "다크",
        "rows_cols": "{rows}행 × {cols}열",
    },
}


def _ws(key: str, lang: str = "en", **kwargs) -> str:
    """Get a web UI string in the given language."""
    strings = _WEB_STRINGS.get(lang, _WEB_STRINGS["en"])
    text = strings.get(key, _WEB_STRINGS["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


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
    async def index(lang: str = "en", theme: str = "light"):
        return HTMLResponse(_get_html_template(lang=lang, theme=theme))

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

        def _count_unique(col: str) -> tuple[str, int]:
            try:
                return col, len(wb.unique_values(col, sheet=sheet))
            except Exception:
                return col, -1

        with ThreadPoolExecutor(max_workers=min(len(columns), _MAX_WORKERS)) as pool:
            results = list(pool.map(_count_unique, columns))
        unique_counts = dict(results)

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
                headers={"Content-Disposition": "attachment; filename=data.xlsx"},
            )

        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=data.{ext}"},
        )

    @app.get("/api/langs")
    async def api_langs():
        return JSONResponse({"langs": SUPPORTED_LANGS})

    return app


def _get_html_template(lang: str = "en", theme: str = "light") -> str:
    def s(key, **kw):
        return _ws(key, lang, **kw)

    is_dark = theme == "dark"
    bg = "#1e1e2e" if is_dark else "#f5f5f5"
    card_bg = "#313244" if is_dark else "#ffffff"
    text_color = "#cdd6f4" if is_dark else "#333333"
    header_bg = "#89b4fa" if is_dark else "#1976D2"
    header_text = "#1e1e2e" if is_dark else "#ffffff"
    hover_bg = "#45475a" if is_dark else "#FFF8E1"
    spotlight_row = "#313244" if is_dark else "#FFF9C4"
    spotlight_focus = "#89b4fa" if is_dark else "#FFD600"
    input_bg = "#313244" if is_dark else "#ffffff"
    input_border = "#45475a" if is_dark else "#ccc"
    btn_primary = "#89b4fa" if is_dark else "#1976D2"
    btn_primary_text = "#1e1e2e" if is_dark else "#ffffff"
    btn_secondary = "#45475a" if is_dark else "#e0e0e0"
    btn_secondary_text = "#cdd6f4" if is_dark else "#333333"
    info_bg = "#181825" if is_dark else "#E3F2FD"
    info_text = "#89b4fa" if is_dark else "#1565C0"
    border_color = "#45475a" if is_dark else "#e0e0e0"

    lang_options = ""
    for code, name in SUPPORTED_LANGS.items():
        selected = " selected" if code == lang else ""
        lang_options += f'<option value="{code}"{selected}>{name} ({code})</option>'

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{s("title")}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: {bg}; color: {text_color}; }}
.header {{ background: {header_bg}; color: {header_text}; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }}
.header h1 {{ font-size: 20px; font-weight: 600; }}
.header .version {{ opacity: 0.8; font-size: 13px; }}
.header-controls {{ display: flex; align-items: center; gap: 10px; }}
.header-controls select {{ padding: 4px 8px; border-radius: 4px; border: 1px solid {input_border}; background: {input_bg}; color: {text_color}; font-size: 13px; }}
.toolbar {{ background: {card_bg}; padding: 12px 24px; border-bottom: 1px solid {border_color}; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
.toolbar select, .toolbar input {{ padding: 6px 12px; border: 1px solid {input_border}; border-radius: 4px; font-size: 14px; background: {input_bg}; color: {text_color}; }}
.toolbar input[type="text"] {{ flex: 1; min-width: 200px; }}
.btn {{ padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
.btn-primary {{ background: {btn_primary}; color: {btn_primary_text}; }}
.btn-primary:hover {{ opacity: 0.9; }}
.btn-secondary {{ background: {btn_secondary}; color: {btn_secondary_text}; }}
.btn-secondary:hover {{ opacity: 0.9; }}
.info-bar {{ padding: 8px 24px; background: {info_bg}; font-size: 13px; color: {info_text}; display: flex; justify-content: space-between; }}
.container {{ padding: 16px 24px; }}
.table-wrapper {{ overflow: auto; background: {card_bg}; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-height: calc(100vh - 240px); }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ position: sticky; top: 0; background: {header_bg}; color: {header_text}; padding: 10px 14px; text-align: left; font-size: 13px; font-weight: 500; white-space: nowrap; z-index: 10; }}
td {{ padding: 8px 14px; border-bottom: 1px solid {border_color}; font-size: 13px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:hover td {{ background: {hover_bg}; }}
tr.spotlight-row td {{ background: {spotlight_row} !important; }}
td.spotlight-focus {{ background: {spotlight_focus} !important; font-weight: 600; }}
.pagination {{ display: flex; justify-content: center; gap: 8px; padding: 16px; }}
.drop-zone {{ border: 2px dashed {border_color}; border-radius: 8px; padding: 60px 20px; text-align: center; cursor: pointer; margin: 20px; background: {card_bg}; }}
.drop-zone:hover {{ border-color: {btn_primary}; background: {info_bg}; }}
.drop-zone h2 {{ color: {text_color}; margin-bottom: 8px; }}
.drop-zone p {{ color: {text_color}; opacity: 0.6; font-size: 14px; }}
.loading {{ text-align: center; padding: 40px; font-size: 16px; color: {text_color}; }}
label {{ display: flex; align-items: center; gap: 4px; font-size: 14px; cursor: pointer; }}
</style>
</head>
<body>
<div class="header">
  <h1>ChaBiao 查表 <span class="version">v{__version__}</span></h1>
  <div class="header-controls">
    <label>{s("lang")}: <select id="langSelect" onchange="switchLang(this.value)">{lang_options}</select></label>
    <label>{s("theme")}: <select id="themeSelect" onchange="switchTheme(this.value)">
      <option value="light"{"" if theme == "light" else ""}>{s("light")}</option>
      <option value="dark"{" selected" if theme == "dark" else ""}>{s("dark")}</option>
    </select></label>
    <span class="version">{s("subtitle")}</span>
  </div>
</div>
<div id="dropZone" class="drop-zone" ondrop="handleDrop(event)" ondragover="event.preventDefault()" onclick="document.getElementById('fileInput').click()">
  <h2>{s("drop_title")}</h2>
  <p>{s("drop_hint")}</p>
  <input type="file" id="fileInput" style="display:none" accept=".xlsx,.xls,.csv,.tsv,.xlsm" onchange="handleFile(this.files[0])">
</div>
<div id="toolbar" class="toolbar" style="display:none">
  <select id="sheetSelect" onchange="loadSheet(this.value)"></select>
  <select id="filterCol"></select>
  <select id="filterMode">
    <option value="contains">{s("contains")}</option>
    <option value="equals">{s("equals")}</option>
    <option value="regex">{s("regex")}</option>
    <option value="search">{s("search_all")}</option>
  </select>
  <input type="text" id="filterInput" placeholder="{s("filter_placeholder")}" onkeydown="if(event.key==='Enter')doFilter()">
  <button class="btn btn-primary" onclick="doFilter()">{s("filter_btn")}</button>
  <button class="btn btn-secondary" onclick="clearFilter()">{s("clear_btn")}</button>
  <label><input type="checkbox" id="spotlightToggle" onchange="toggleSpotlight()"> {s("spotlight")}</label>
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
let currentLang = '{lang}';
let currentTheme = '{theme}';

async function handleFile(file) {{
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {{
    const resp = await fetch('/api/open', {{method: 'POST', body: formData}});
    const data = await resp.json();
    if (data.success) {{
      currentFileId = data.data.file_id;
      document.getElementById('dropZone').style.display = 'none';
      document.getElementById('toolbar').style.display = 'flex';
      document.getElementById('infoBar').style.display = 'flex';
      document.getElementById('tableWrapper').style.display = 'block';
      const sheetSelect = document.getElementById('sheetSelect');
      sheetSelect.innerHTML = '';
      data.data.sheets.forEach(s => {{ const o = document.createElement('option'); o.value = s; o.textContent = s; sheetSelect.appendChild(o); }});
      const r = currentLang === 'zh' ? `{{data.data.info.rows}} 行 × ${{data.data.info.columns}} 列` : `${{data.data.info.rows}} rows × ${{data.data.info.columns}} cols`;
      document.getElementById('fileInfo').textContent = `${{data.data.file_id}} | ${{r}}`;
      await loadColumns();
      await loadData();
    }}
  }} catch(e) {{ alert('Error: ' + e.message); }}
}}

function handleDrop(e) {{
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  handleFile(file);
}}

async function loadColumns() {{
  const resp = await fetch(`/api/columns/${{encodeURIComponent(currentFileId)}}`);
  const data = await resp.json();
  const sel = document.getElementById('filterCol');
  sel.innerHTML = '';
  data.columns.forEach(c => {{ const o = document.createElement('option'); o.value = c; o.textContent = c + ` (${{data.unique_counts[c]}})`; sel.appendChild(o); }});
}}

async function loadData(start=0) {{
  currentPage = start;
  const resp = await fetch(`/api/data/${{encodeURIComponent(currentFileId)}}?start=${{start}}&limit=${{pageSize}}`);
  const data = await resp.json();
  renderTable(data);
  renderPagination(data);
}}

function renderTable(data) {{
  const thead = document.getElementById('tableHead');
  const tbody = document.getElementById('tableBody');
  thead.innerHTML = '<tr>' + data.columns.map(c => `<th>${{c}}</th>`).join('') + '</tr>';
  tbody.innerHTML = data.rows.map((row, i) =>
    '<tr onclick="onRowClick(' + i + ')" id="row-' + i + '">' +
    data.columns.map(c => `<td class="cell" data-col="${{c}}" data-row="${{i}}">${{row[c] !== null && row[c] !== undefined ? row[c] : ''}}</td>`).join('') +
    '</tr>'
  ).join('');
}}

function renderPagination(data) {{
  const total = data.total;
  const pages = Math.ceil(total / pageSize);
  const div = document.getElementById('pagination');
  if (pages <= 1) {{ div.innerHTML = ''; return; }}
  let html = '';
  for (let i = 0; i < pages && i < 20; i++) {{
    html += `<button class="btn ${{i===currentPage?'btn-primary':'btn-secondary'}}" onclick="loadData(${{i*pageSize}})">${{i+1}}</button>`;
  }}
  if (pages > 20) html += `<span>... ${{pages}} pages</span>`;
  div.innerHTML = html;
}}

async function doFilter() {{
  const col = document.getElementById('filterCol').value;
  const keyword = document.getElementById('filterInput').value;
  const mode = document.getElementById('filterMode').value;
  let url;
  if (mode === 'search') {{
    url = `/api/search/${{encodeURIComponent(currentFileId)}}?keyword=${{encodeURIComponent(keyword)}}`;
  }} else if (mode === 'contains') {{
    url = `/api/filter/${{encodeURIComponent(currentFileId)}}?column=${{encodeURIComponent(col)}}&contains=${{encodeURIComponent(keyword)}}`;
  }} else if (mode === 'equals') {{
    url = `/api/filter/${{encodeURIComponent(currentFileId)}}?column=${{encodeURIComponent(col)}}&equals=${{encodeURIComponent(keyword)}}`;
  }} else {{
    url = `/api/filter/${{encodeURIComponent(currentFileId)}}?column=${{encodeURIComponent(col)}}&regex=${{encodeURIComponent(keyword)}}`;
  }}
  const resp = await fetch(url);
  const data = await resp.json();
  renderTable(data);
  document.getElementById('filterInfo').textContent = `{s("filter_results", count="")}${{data.total}}`;
}}

async function clearFilter() {{
  document.getElementById('filterInput').value = '';
  document.getElementById('filterInfo').textContent = '';
  await loadData();
}}

function toggleSpotlight() {{
  spotlightOn = document.getElementById('spotlightToggle').checked;
  if (!spotlightOn) clearSpotlight();
}}

function onRowClick(rowIdx) {{
  if (!spotlightOn) return;
  spotlightRow = rowIdx;
  applySpotlight();
}}

function applySpotlight() {{
  clearSpotlight();
  if (spotlightRow < 0) return;
  const rows = document.getElementById('tableBody').querySelectorAll('tr');
  rows.forEach((row, i) => {{
    if (i === spotlightRow) {{
      row.classList.add('spotlight-row');
      row.querySelectorAll('td').forEach(td => td.classList.add('spotlight-focus'));
    }}
  }});
}}

function clearSpotlight() {{
  document.querySelectorAll('.spotlight-row').forEach(r => r.classList.remove('spotlight-row'));
  document.querySelectorAll('.spotlight-focus').forEach(td => td.classList.remove('spotlight-focus'));
}}

async function loadSheet(sheet) {{
  await loadColumns();
  await loadData();
}}

function switchLang(lang) {{
  currentLang = lang;
  window.location.href = '/?lang=' + lang + '&theme=' + currentTheme;
}}

function switchTheme(theme) {{
  currentTheme = theme;
  window.location.href = '/?lang=' + currentLang + '&theme=' + theme;
}}
</script>
</body>
</html>"""


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
