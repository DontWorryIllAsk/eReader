# AGENTS.md - eReader 项目编码指南

## 项目概述

eReader 是一个 Windows 桌面 EPUB 阅读器，参考 Apple Books 简化版，核心功能：
1. **EPUB 阅读**：支持打开和阅读 EPUB 格式电子书
2. **阅读自定义**：换字体、调字号、多种底色（白天、晚上、护眼等）
3. **书库管理**：管理本地电子书库
4. **本地导入**：支持从电脑拖入或文件选择导入
5. **图书标注**：文字高亮、划线、书签等

## 构建 / 测试 / Lint 命令

Python 3.12，venv 位于 `.venv/`。

| 操作 | 命令 | 说明 |
|------|------|------|
| 激活 venv | `.venv\Scripts\Activate.ps1` | PowerShell |
| 安装依赖 | `pip install -r requirements.txt` | 需设代理 |
| 运行全部测试 | `pytest tests/ -v` | |
| 运行单个测试 | `pytest tests/test_epub_reader.py -v` | |
| 覆盖率 | `pytest --cov=src tests/` | 目标 ≥ 80% |
| 启动应用 | `python -m src.main` | |
| Python 路径 | `d:\myapps\python\Python312\python.exe` | 系统 Python |
| pip 镜像 | `-i https://pypi.tuna.tsinghua.edu.cn/simple` | 清华镜像 |

### 代理注意事项

公司代理 `proxy.huawei.com:8080` 会拦截 HTTPS，pip 安装时需要：
```powershell
$env:HTTP_PROXY="http://proxy.huawei.com:8080"; $env:HTTPS_PROXY="http://proxy.huawei.com:8080"; $env:NO_PROXY=""
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

## 项目结构

```
eReader/
├── src/
│   ├── main.py                  # 应用入口
│   ├── app.py                   # QApplication 管理
│   ├── models/
│   │   ├── database.py          # SQLite 数据库管理
│   │   ├── book.py              # Book 数据模型 + Repository
│   │   └── annotation.py        # Annotation/Bookmark 模型 + Repository
│   ├── readers/
│   │   ├── epub_reader.py       # EPUB 解析（ebooklib）
│   │   └── reader_widget.py     # 阅读器 QWidget（WebEngine 渲染）
│   ├── library/
│   │   ├── main_window.py       # 主窗口
│   │   ├── library_widget.py    # 书库界面（P2）
│   │   └── import_handler.py    # 导入/拖入处理（P3）
│   ├── settings/
│   │   ├── settings.py          # 阅读设置管理（ReaderSettings）
│   │   └── settings_widget.py   # 设置面板（P2）
│   ├── annotations/
│   │   ├── annotation_widget.py # 标注工具栏（P4）
│   │   └── bookmark_manager.py  # 书签管理（P4）
│   └── utils.py                 # 公共工具
├── resources/
│   ├── icons/                   # 图标资源
│   └── styles/                  # QSS 样式表
├── tests/                       # pytest 测试
├── .venv/                       # Python 虚拟环境
├── pyproject.toml
├── requirements.txt
└── AGENTS.md
```

## 编码规范

### 通用原则

- 编写代码的同时编写单元测试代码，写完代码后必须通过单元测试
- 修改代码后必须通过回归测试，确保不引入额外问题
- 不要在代码中硬编码敏感信息（用户名、口令、API Key 等），使用环境变量或配置文件
- 可以修改项目工作目录内的文件；在工作目录外可以增加文件，但不要删除和修改非项目生成的文件
- 如果对指令不清楚，主动与用户确认
- 复杂任务建议用 PLAN 模式，用户确认后再开始执行
- 定期把工作进展记录到文件中

### Imports / 导入

- 标准库导入 → 第三方库导入 → 本地模块导入，各组之间空一行
- 禁止使用通配符导入（`from module import *`）
- 优先使用绝对导入，避免循环依赖

### 格式化

- 缩进：4 个空格
- 行宽上限：120 字符
- 文件末尾保留一个空行
- 删除行尾空白字符

### 类型与命名约定

| 元素 | 风格 | 示例 |
|------|------|------|
| 类名 | PascalCase | `EpubReader`, `ReaderWidget` |
| 函数/方法 | snake_case | `load_book()`, `get_chapter()` |
| 变量 | snake_case | `chapter_index`, `file_path` |
| 常量 | UPPER_SNAKE_CASE | `ITEM_DOCUMENT`, `THEME_COLORS` |
| 私有成员 | 前缀下划线 | `_extract_chapters()`, `_setup_ui()` |
| 模块/文件名 | snake_case | `epub_reader.py`, `reader_widget.py` |
| dataclass | PascalCase | `Book`, `Annotation`, `ReaderSettings` |

### 类型注解

- 所有公开函数必须包含类型注解（参数 + 返回值）
- 使用 `str | Path` 表示多种类型
- 使用 `| None` 表示可选类型

### 错误处理

- 使用具体的异常类型，不要裸 `except`
- 错误消息应包含上下文信息（如文件路径、参数值）
- 在函数边界验证输入参数（如 `FileNotFoundError` 检查）

### 文档

- 公开类和函数必须有 docstring（Google Style）
- 复杂算法必须附带行内注释解释"为什么"，而非"做什么"

## 测试规范

### 单元测试

- 每个新功能/模块必须同时编写对应的单元测试
- 测试文件放在 `tests/` 目录，命名规则：`test_<module>.py`
- 使用 pytest fixture 管理测试资源
- 测试类按功能分组：`TestInit`, `TestConvert`, `TestEdgeCases`

### 回归测试

- 每次修改代码后必须运行完整回归测试套件：`pytest tests/ -v`
- 修复 Bug 时必须同时添加回归测试
- 保持回归测试集持续更新，不允许随意删除已有回归测试

### 测试覆盖率

- 目标：核心模块行覆盖率 ≥ 80%
- 关键路径（EPUB 解析、数据库操作、设置管理）覆盖率 ≥ 90%

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| GUI | PySide6 | Qt for Python，跨平台桌面框架 |
| EPUB 解析 | ebooklib | Python EPUB 解析库 |
| HTML 渲染 | QWebEngineView | Chromium 内核渲染 EPUB 内容 |
| 数据存储 | SQLite | 嵌入式数据库，存储书库/标注/设置 |
| HTML 解析 | BeautifulSoup4 + lxml | 提取章节标题和正文 |
| 测试 | pytest + pytest-cov | |

## 开发进度

### P1 - 核心阅读器 ✅

- [x] 项目骨架（目录结构、pyproject.toml、requirements.txt）
- [x] SQLite 数据库模块（books/annotations/bookmarks/settings 表）
- [x] Book/Annotation/Bookmark 数据模型 + Repository
- [x] EPUB 解析器（章节提取、元数据、目录、封面）
- [x] 阅读器 Widget（WebEngine 渲染、翻页、章节导航）
- [x] 主窗口框架（菜单栏、工具栏、状态栏）
- [x] 应用入口（main.py + app.py）
- [x] 单元测试（50 个测试全部通过）

### P2 - 阅读自定义 ✅

- [x] 设置面板 Widget（字体/字号/底色选择）
- [x] 设置持久化到数据库
- [x] 主题切换（白天/晚上/护眼/绿色）

### P3 - 书库管理 + 本地导入 ✅

- [x] 书库界面（网格/列表视图）
- [x] 文件拖入导入
- [x] 文件选择对话框导入
- [x] 封面提取与显示

### P3.5 - 全屏阅读模式 ✅

- [x] F11 / 菜单 / 工具栏切换全屏
- [x] Esc 退出全屏
- [x] 全屏时隐藏菜单栏、主工具栏、设置面板
- [x] 阅读器工具栏自动隐藏，鼠标移至顶部时显示
- [x] 阅读器工具栏"Exit Fullscreen"按钮

### P3.6 - 阅读进度持久化 ✅

- [x] ReaderWidget 输出 reading_progress_changed 信号（chapter_index, position_in_chapter）
- [x] load_book() 支持传入 chapter_index 和 position_in_chapter 恢复阅读位置
- [x] 翻页时自动保存进度到数据库
- [x] 返回书库和关闭窗口时保存进度
- [x] 重新打开图书时跳转到上次阅读位置
- [x] 单元测试（7 个阅读进度测试）

### P4 - 标注功能 ✅

- [x] 文字选择与高亮（JS getSelectedTextInfo + applyAnnotation）
- [x] 划线标注（underline/strikethrough）
- [x] 书签添加/管理（BookmarkManager 面板）
- [x] 标注持久化（AnnotationRepository 数据库读写）
- [x] 标注工具栏（AnnotationToolBar 浮动工具栏）
- [x] 单元测试（16 个标注/书签 UI 测试）

### P5 - 整体打磨 ✅

- [x] QSS 主题美化（4 套主题：Light/Dark/Sepia/Green，全局 QSS 样式表）
- [x] 图标资源（SVG 矢量图标，13 个图标：library/import/settings/fullscreen/bookmark/bookmarks/highlight/underline/strikethrough/delete/exit-fullscreen/prev-chapter/next-chapter）
- [x] 键盘快捷键完善（Ctrl+1/2/3/4 切换主题，Home/End 首尾页，Ctrl+Home/End 首尾章节）
- [x] 窗口状态记忆（分割器布局、上次打开的图书自动恢复）
- [x] 单元测试（7 个新增测试，共 108 个测试全部通过）

### P6 - 大文件性能优化 ✅

- [x] EPUB 加载优化：懒加载章节内容、快速正则提取标题、图片缓存
- [x] HTML 预处理：合并冗余 `<span class="bookspan">` 和 `<span id="cb1-X">`，DOM 减少 67.8%
- [x] 图片解析优化：正则替换替代 BeautifulSoup，避免重复解析
- [x] 分页渲染：`getClientRects()` 行级分页 + `clipPath: inset()` 精确裁剪，翻页无缝衔接
- [x] 阅读进度保存防抖：2 秒防抖避免每次翻页写 SQLite，关闭/返回时立即 flush
- [x] 单元测试（108 个测试全部通过）

#### P6 性能优化技术要点

**问题**：Architecting Modern Systems（21.6 MB EPUB，19 章，最大章节 2MB HTML）打开极慢、翻页卡顿。

**根因**：
1. `EpubReader.__init__` 用 BeautifulSoup 解析每章完整 HTML 仅提取标题，19 章耗时 11.6s
2. `_extract_body_content` + `resolve_images` 各用 BS4 解析一次，2MB 章节耗时 10.3s
3. 该 EPUB 每个词/标点都包裹在 `<span class="bookspan" id="book.X.Y">` 中，2MB 章节有 33,484 个标签（88% 冗余）
4. 每次翻页触发 SQLite 写入保存阅读进度

**优化措施**：

1. **懒加载章节**（`epub_reader.py`）：`Chapter` 对象创建时不加载内容，`ensure_loaded()` 在 `get_chapter()` 时按需加载。初始化时间 11.6s → 0.97s。
   - `Chapter` dataclass 新增 `_item_id`, `_item_name`, `_loaded` 字段
   - `_extract_chapters()` 只提取 item_id 和标题，不调用 `get_content()`
   - `get_chapter(index)` 调用 `ensure_loaded()` 按需加载

2. **快速标题提取**（`epub_reader.py`）：`_extract_chapter_title_fast()` 先查 TOC，再用正则匹配前 10KB HTML 中的 `<h1>`-`<h3>` 标签，避免 BS4 解析整个 HTML。

3. **图片缓存**（`epub_reader.py`）：`_build_image_cache()` 在初始化时构建 `name → item` 字典，`_find_image_item()` 优先查缓存，O(1) 查找。

4. **正则替代 BS4**（`epub_reader.py`）：`resolve_images()` 用 `_IMG_SRC_RE` 和 `_SVG_HREF_RE` 正则替换 `<img src>` 和 `<image xlink:href>`，不再解析整个 HTML。`_extract_body_content()` 用 `_BODY_RE` 正则提取 `<body>` 内容。`epub_reader.py` 不再导入 BeautifulSoup。

5. **HTML 预处理合并冗余 span**（`reader_widget.py`）：
   - `_BOOKSPAN_RE`：移除 `<span xmlns=... class="bookspan" id="book.X.Y">text</span>` 包装，保留文本
   - `_LINE_SPAN_RE`：移除代码块中 `<span id="cb1-X">text</span>` 行包装，保留文本和语法高亮 span
   - 效果：22.7MB → 7.3MB（减少 67.8%），DOM 节点从 33K 降至 18K

6. **分页与渲染**（`reader_widget.py`）：
   - `computePageBreaks()`：使用 `range.getClientRects()` 行级分页（精确到每行文字），配合 span 合并后的精简 DOM 性能足够
   - `showPage()`：`transform: translateY()` 定位 + `clipPath: inset()` 精确裁剪可见区域，确保翻页无缝衔接、无内容重叠、无行截断
   - ⚠️ **`clipPath` 不可移除**：`overflow: hidden` 只能裁剪到视口边界，无法精确裁剪到分页断点，移除会导致内容重叠和行截断

7. **阅读进度保存防抖**（`main_window.py`）：
   - `_on_reading_progress_debounced()`：2 秒 QTimer 防抖，翻页时不立即写 SQLite
   - `_flush_reading_progress()`：关闭窗口、返回书库时立即 flush，确保不丢失进度
   - `_pending_progress`：暂存最新的 (chapter_index, position) 元组

#### P6 关键约束（后续改动必须遵守）

- **`clipPath: inset()` 必须保留**：移除会导致翻页内容重叠和行截断
- **`getClientRects()` 行级分页必须保留**：块级元素分页（`querySelectorAll`）会导致跨页段落内容重复
- **span 合并正则必须保留**：移除会导致大 EPUB 的 DOM 节点数爆炸，翻页卡顿
- **阅读进度防抖必须保留**：移除会导致每次翻页写 SQLite，影响翻页响应速度

### P7 - 书库搜索与无限滚动 ✅

- [x] 图书搜索框（工具栏 QLineEdit，按书名关键字搜索，大小写不敏感）
- [x] BookRepository.search_by_title() SQL LIKE 查询
- [x] 无限滚动加载（滚动到底部自动加载下一批，每批 30 本）
- [x] 单元测试（5 个搜索测试，共 113 个测试全部通过）

### P5.1 - Windows EXE 打包与图标 ✅

- [x] PyInstaller 打包（eReader.spec，onedir 模式，console=False）
- [x] 安装脚本（dist/install.ps1：复制到 LocalAppData、创建快捷方式、注册 .epub 文件关联）
- [x] 应用图标（blue book SVG → 多尺寸 ICO → 嵌入 EXE 资源）

#### EXE 图标关键技术要点

**问题**：PyInstaller 默认将 ICO 中的所有图标转为 PNG 格式嵌入 EXE，而 Windows Explorer 对 16x16 PNG 图标渲染不佳，导致小图标显示异常（显示为旧图标/默认图标）。

**解决方案**：生成混合格式的 ICO 文件（小尺寸用 DIB，大尺寸用 PNG），然后在 `eReader.spec` 中指定该 ICO，让 PyInstaller 在构建时原样嵌入。

**构建流程**：
1. `python generate_icon.py` — 从 SVG 渲染各尺寸图标，生成 `resources/icons/app_icon.ico`（16/24/32/48px DIB + 64/128/256px PNG）
2. `pyinstaller eReader.spec --noconfirm` — 打包 EXE，PyInstaller 的 `CopyIcons_FromIco` 会原样读取 ICO 中的 DIB/PNG 数据嵌入资源
3. `powershell -ExecutionPolicy Bypass -File dist/install.ps1` — 安装到 LocalAppData 并创建快捷方式

**关键文件**：
- `generate_icon.py` — SVG → ICO 转换，`pixmap_to_dib()` 函数将 QPixmap 转为 Windows DIB 格式（BITMAPINFOHEADER + BGRA 像素 + AND 掩码）
- `eReader.spec` — `icon=str(project_root / 'resources' / 'icons' / 'app_icon.ico')`
- `replace_icon.py` — 事后修改 EXE 图标资源的脚本（**已废弃，不要使用**）

**已踩过的坑**：

1. **❌ 事后用 `UpdateResourceW` 修改 EXE 图标**：`BeginUpdateResourceW` + `EndUpdateResourceW` 会重建整个 PE 文件，丢弃 PyInstaller 追加在文件末尾的 PKG overlay 数据，导致 EXE 无法启动（报错 "could not load PyInstaller's embedded Pkg archive"）。必须在 PyInstaller 构建时就嵌入图标。

2. **❌ 事后用 pefile 修改 PE 资源**：`pefile.PE().__data__` 不包含 PE overlay 数据，写回文件时同样会丢失 PKG archive，导致 EXE 无法启动。

3. **❌ PyInstaller 对 ICO 中的 DIB 格式处理**：经测试，PyInstaller 的 `CopyIcons_FromIco` 会原样读取 ICO 中的图像数据（不做格式转换），所以 ICO 中包含 DIB 格式的小图标会被正确嵌入。但 PyInstaller 自己的默认图标（bootloader 中的 icon-windowed.ico）只有 PNG 格式。

4. **✅ 正确方案**：在 `eReader.spec` 中指定包含 DIB 小图标的 ICO 文件，让 PyInstaller 在构建流程中嵌入（顺序：复制 bootloader → 嵌入图标 → 追加 PKG overlay），这样既不破坏 EXE，又能保证小图标是 DIB 格式。

**Windows 图标缓存问题**：修改 EXE 图标后，Explorer 可能仍显示旧图标。解决方法：
```powershell
# 方法1：清除图标缓存并重启 Explorer
Stop-Process -Name explorer -Force
Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*" -Force -ErrorAction SilentlyContinue
Start-Process explorer

# 方法2：重启电脑

# 方法3：运行 ie4uinit.exe -show（效果有限）
ie4uinit.exe -show
```

## Git 仓库

- **远程仓库**：https://github.com/william22076/eReader
- **Git 路径**：`C:\Program Files\Git\cmd\git.exe`（当前终端 PATH 未包含，需用完整路径）
- **Git 用户**：William <william22076@users.noreply.github.com>

## 版本历史

### v1.0.0 (2026-06-27)

首次发布，包含全部 P1-P7 功能。

| 阶段 | 功能 | 测试数 |
|------|------|--------|
| P1 | 核心阅读器（EPUB 解析、WebEngine 渲染、翻页、章节导航） | 50 |
| P2 | 阅读自定义（字体/字号/4 种底色主题） | - |
| P3 | 书库管理 + 本地导入（网格视图、拖入/选择导入、封面显示） | - |
| P3.5 | 全屏阅读模式（F11/Esc、工具栏自动隐藏） | - |
| P3.6 | 阅读进度持久化（2 秒防抖、关闭时 flush） | 7 |
| P4 | 标注功能（高亮/划线/书签、浮动工具栏、持久化） | 16 |
| P5 | 整体打磨（QSS 4 主题、SVG 图标、快捷键、窗口记忆） | 7 |
| P5.1 | Windows EXE 打包与图标（PyInstaller、DIB/PNG ICO、安装脚本） | - |
| P6 | 大文件性能优化（懒加载、span 合并、正则替代 BS4、行级分页） | 28 |
| P7 | 书库搜索与无限滚动（关键字搜索、每批 30 本滚动加载） | 5 |

**总计**：113 个单元测试全部通过
