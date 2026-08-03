# Wind Farm Coordinate Verifier (v2.0) · 风电场坐标校验工具

A lightweight, local-first tool for **manually verifying and correcting wind-turbine
coordinates** against high-resolution satellite imagery (Esri World Imagery basemap).
It is **farm-agnostic**: use it for *any* wind farm, not just 640358.

一个轻量、本地运行的工具，用于在**高分辨率卫星影像**（Esri 卫星底图）上**人工核对并修正风机坐标**。
**不限定风电场**：适用于任意风电场，不局限于 640358。

> This is **Path 1 — Manual verification**, now generalized + packaged as a
> one-click tool. The automated image-based detection tool (YOLO / SAM) is a
> separate effort (Path 2/3).
>
> 本项目为 **路径 1 —— 人工校验**，已通用化并打包为“一键即用”工具。
> 基于图像的自动识别工具（YOLO / SAM）为另一独立工作（路径 2/3）。

---

## What it does · 功能简介

- Upload a turbine list as **CSV** or **PDF** (a turbine layout sheet)
  · 上传风机清单（**CSV** 或 **PDF** 排布图）
- See every turbine on a satellite basemap (map auto-fits to your data bounds)
  · 在卫星底图上查看每台风机（地图自动缩放到数据范围）
- Click a row → fly to the original location
  · 点击某一行 → 地图飞至该风机原始位置
- **✏️ Edit** → click the real turbine on the map → records corrected coordinates + deviation (meters)
  · **✏️ 编辑** → 在地图上点击真实风机位置 → 记录修正坐标与偏差（米）
- **OK** → confirm the original is correct (0 m)
  · **OK** → 确认原始坐标正确（偏差 0 米）
- **↺ Reset** → clear a row to re-correct it
  · **↺ 重置** → 清除该行，可重新修正
- **Undo** (⌘/Ctrl+Z) → revert the last correction
  · **撤销**（⌘/Ctrl+Z）→ 回退上一次修正
- Auto-advances to the next unverified turbine; live OK / Review / Offset KPIs
  · 自动跳转到下一台未校验风机；实时显示 合格 / 复核 / 偏移 统计
- Auto-saves **per farm** to the browser; **Export** a re-importable corrected CSV
  · 按风电场自动保存于浏览器；**导出**可再次导入的修正后 CSV

---

## The one-click tool (recommended) · 一键工具（推荐）

`wind-farm-verifier.html` is a **single self-contained file** — Leaflet + pdf.js are
inlined, so it works by **double-clicking it** (opens in your default browser, no
server, no internet for assets; map tiles do need internet). PDFs are parsed
**in-browser**, so there is no backend dependency at all.

`wind-farm-verifier.html` 是一个**单文件、自包含**的工具 —— Leaflet 与 pdf.js 已内嵌，
**双击即可打开**（默认浏览器中运行，无需服务器、无需联网加载资源；地图瓦片需联网）。
PDF 在**浏览器内直接解析**，因此完全不依赖后端服务。

**Just double-click `wind-farm-verifier.html` and upload your CSV/PDF. That's it.**
**只需双击 `wind-farm-verifier.html`，上传 CSV/PDF 即可，无需其他操作。**

Download / 下载：
https://github.com/nekdil566/gw640358-verifier/raw/main/wind-farm-verifier.html

---

## Run as a dev server (optional) · 以开发服务器运行（可选）

The dev source `index.html` references `lib/` assets, so serve it with the bundled
Flask app (or any static server). Convenient when you want to hot-edit `index.html`
and rebuild.

开发版 `index.html` 引用 `lib/` 资源，需用自带的 Flask 服务（或任意静态服务器）托管，
便于修改 `index.html` 后重新构建。

```bash
cd wind-turbine-verifier
pip install -r requirements.txt
python3 server.py            # http://127.0.0.1:8000
# or: bash start.sh           # creates a venv and starts on :8000
```

> Note: `index.html` expects `lib/pdfjs/*.js` to exist (download via build step).
> `wind-farm-verifier.html` is fully standalone and does not need these.
>
> 注意：`index.html` 需要 `lib/pdfjs/*.js` 存在（通过构建步骤下载）。
> `wind-farm-verifier.html` 为完全独立文件，无需这些依赖。

## Build the standalone file · 构建独立文件

```bash
python3 build.py             # -> wind-farm-verifier.html (single file, inlined assets)
```

Requires `lib/leaflet.js`, `lib/leaflet.css`, `lib/pdfjs/pdf.min.js`,
`lib/pdfjs/pdf.worker.min.js` to be present (provided in this repo).

需要 `lib/` 下存在 Leaflet 与 pdf.js 资源（本仓库已包含）。

---

## CSV format · CSV 格式

Minimum columns (header names are case-insensitive aliases) · 最少列（表头名称不区分大小写，支持别名）：

```csv
id,lat,lon
6403580001,37.3733,106.4133
```

Accepted aliases · 支持的别名：
- **ID**: `wtid`, `id`, `turbine_id`
- **Latitude 纬度**: `lat`, `latitude`, `lat_corrected`, `corrected_lat`
- **Longitude 经度**: `lon`, `longitude`, `lon_corrected`, `corrected_lon`

If the CSV already carries corrected coordinates, they are restored as the baseline.
若 CSV 已包含修正坐标，将作为初始基线载入。

---

## PDF import · PDF 导入

Upload a turbine layout PDF. Coordinates are extracted **in-browser** with pdf.js
(no server needed) using the same pattern as before: a 4+ digit id followed by two
decimal coordinates (lat in [-90,90], lon in [-180,180]).

上传风机排布 PDF。坐标由 **pdf.js 在浏览器内** 提取（无需服务器），识别规则同上：
4 位及以上编号 + 两个小数坐标（纬度 ∈ [-90,90]，经度 ∈ [-180,180]）。

---

## Farm name · 风电场名称

The farm name is editable in the top bar. It is derived from the uploaded file name
(unless you type your own) and used for **per-farm storage** and the export filename.
Nothing is auto-restored on load — upload your CSV/PDF each session.

风电场名称可在顶部栏编辑。默认取自上传文件名（也可手动输入），用于
**按风电场分别保存**及导出文件名。打开时不自动恢复数据 —— 每次需重新上传 CSV/PDF。

---

## Status badges · 状态标识

| Badge 标识 | Meaning 含义 |
|-------|---------|
| `ok` 合格 | deviation 0–20 m 偏差 0–20 米 |
| `wn` 复核 | deviation 20–100 m 偏差 20–100 米 |
| `er` 偏移 | deviation > 100 m 偏差大于 100 米 |
| `na` 未核 | not yet verified 尚未校验 |

---

## Testing · 测试

Real browser end-to-end check (headless Chrome, requires Google Chrome installed) ·
真实浏览器端到端测试（无头 Chrome，需安装 Google Chrome）：

```bash
npm install puppeteer-core
node test_e2e.js            # builds nothing; tests wind-farm-verifier.html
```

---

## Repository layout · 仓库结构

```
index.html            # dev verifier UI (references lib/ assets) 开发版界面
wind-farm-verifier.html  # STANDALONE one-click deliverable (inlined assets) 独立一键文件
build.py              # inlines assets -> wind-farm-verifier.html 构建脚本
test_e2e.js           # headless-Chrome end-to-end test 端到端测试
server.py             # optional Flask backend (legacy PDF path / static serve) 可选后端
lib/                  # bundled Leaflet + pdf.js 内嵌资源
analyze.py            # batch diagnostic vs OSM 批量诊断
auto_verify.py        # earlier classical-CV attempt (superseded) 早期 CV 尝试（已弃用）
requirements.txt
```

---

## Roadmap · 路线图

- [x] Generalized, farm-agnostic manual verifier · 通用化、适用于任意风电场的手动校验
- [x] One-click standalone HTML (in-browser PDF parsing, no server) · 一键独立 HTML（浏览器内解析 PDF，无需服务器）
- [ ] **Separate repo** `gw640358-auto`: automated turbine detection from imagery (YOLO/SAM) · 独立仓库 `gw640358-auto`：基于影像的自动风机识别（YOLO/SAM）
