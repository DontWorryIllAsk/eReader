# eReader — 类 iBooks 的 Windows EPUB 阅读器

eReader 是一款面向 Windows 的简洁 EPUB 电子书阅读器，界面灵感来源于 Apple Books，支持书库管理、阅读自定义、标注与进度持久化。

## 解决什么问题 / 适合谁

适合希望在 Windows 上拥有一款**轻量、原生、可离线使用**的 EPUB 阅读器的用户。它不需要复杂配置，打开即可管理书库、阅读电子书、做高亮批注，并能记住阅读位置和个性化设置。

## 核心特性

- **EPUB 阅读**：基于 ebooklib 解析内容，使用 QWebEngineView 渲染，支持章节导航、翻页、全屏阅读。
- **书库管理**：网格视图展示封面、书名和作者；支持文件拖入导入与文件选择对话框导入；自动提取并缓存封面。
- **阅读自定义**：自由切换字体、字号、行间距；提供白天、晚上、护眼、绿色四种阅读主题。
- **标注与书签**：支持文字高亮、红色下划线、删除线标注；可添加书签并通过浮动工具栏快速管理。
- **进度持久化**：自动保存阅读进度（2 秒防抖），重新打开图书时回到上次位置。
- **键盘快捷键**：方向键/PageUp/PageDown 翻页、Ctrl+Left/Right 切换章节、F11 全屏、Ctrl+1/2/3/4 切换主题等。
- **Windows 可执行文件**：通过 PyInstaller 打包为独立 EXE，支持 .epub 文件关联与安装脚本。

## 技术栈

- **语言**：Python 3.12+
- **GUI 框架**：PySide6（Qt Widgets + Qt WebEngine）
- **EPUB 解析**：ebooklib
- **HTML 处理**：BeautifulSoup4 + lxml
- **数据持久化**：SQLite
- **测试**：pytest + pytest-cov + pytest-qt
- **打包**：PyInstaller

## 安装与运行

```bash
# 1. 进入项目目录
cd eReader-master

# 2. 创建并激活虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
python -m src.main

# 或直接打开指定图书
python -m src.main "C:\path\to\book.epub"
```

### 运行测试

```bash
pytest tests/ -v
pytest --cov=src tests/          # 覆盖率报告（目标 ≥ 80%）
```

### 打包为 Windows 可执行文件

```bash
# 确保已安装 PyInstaller
pip install pyinstaller

pyinstaller eReader.spec
# 输出目录：dist/eReader/
```

## 主要文件与职责

| 文件 / 目录 | 职责 |
|-------------|------|
| `src/main.py` | 应用入口，初始化并运行 `EReaderApp` |
| `src/app.py` | `EReaderApp` 主控制器，管理 QApplication、数据库、主题与主窗口 |
| `src/library/main_window.py` | 主窗口：工具栏、菜单、视图切换、快捷键、导入与打开图书 |
| `src/library/library_widget.py` | 书库网格视图、搜索框、无限滚动加载 |
| `src/library/import_handler.py` | 处理 EPUB 文件导入、封面提取与元数据保存 |
| `src/readers/epub_reader.py` | EPUB 解析器：元数据、章节、目录、图片、懒加载 |
| `src/readers/reader_widget.py` | 阅读器控件：渲染、分页、标注交互、进度同步 |
| `src/models/database.py` | SQLite 数据库连接与表初始化 |
| `src/models/book.py` | `Book` 数据模型与 `BookRepository` |
| `src/models/annotation.py` | 标注与书签模型及其 Repository |
| `src/settings/settings.py` | 阅读设置数据类（字体、字号、主题、行间距） |
| `src/settings/settings_repository.py` | 设置读写持久化 |
| `src/settings/theme_manager.py` | 主题应用与 QSS 样式管理 |
| `src/annotations/annotation_widget.py` | 浮动标注工具栏 |
| `src/annotations/bookmark_manager.py` | 书签管理面板 |
| `resources/icons/` | 应用图标与 SVG 图标资源 |
| `tests/` | 单元测试（当前 113 个测试全部通过） |

## 项目亮点

项目中最具挑战也最有价值的是**大文件 EPUB 的阅读性能优化**：通过章节懒加载、HTML 预处理合并冗余 span、正则替代 BeautifulSoup 解析、以及基于 `getClientRects()` 的精确行级分页，把大型 EPUB 的初始化时间从 11.6 秒降到约 1 秒。此外，对标注、进度、主题等细节的打磨，让这款阅读器在 Windows 上也能拥有接近原生阅读应用的体验。
