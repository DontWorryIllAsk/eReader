# eReader Changelog

## v1.0.0 (2026-06-26)

### P1 - 核心阅读器
- EPUB 打开与阅读（ebooklib 解析 + QWebEngineView 渲染）
- 章节导航（下拉框选择、上一章/下一章按钮）
- 翻页（左右箭头键、PageUp/PageDown）
- 主窗口框架（菜单栏、工具栏、状态栏）

### P2 - 阅读自定义
- 字体选择、字号调节
- 4 种阅读底色（白天/晚上/护眼/绿色）

### P3 - 书库管理与导入
- 书库网格视图（封面、标题、作者）
- 文件拖入导入、文件选择对话框导入
- 封面提取与显示

### P3.5 - 全屏阅读模式
- F11 / 菜单 / 工具栏切换全屏
- Esc 退出全屏
- 全屏时工具栏自动隐藏，鼠标移至顶部显示

### P3.6 - 阅读进度持久化
- 翻页时自动保存进度（2 秒防抖）
- 关闭窗口/返回书库时立即保存
- 重新打开图书时跳转到上次阅读位置

### P4 - 标注功能
- 文字选择与高亮（黄色背景）
- 划线标注（红色下划线/删除线）
- 书签添加/管理（BookmarkManager 面板）
- 标注持久化（AnnotationRepository 数据库读写）
- 标注工具栏（AnnotationToolBar 浮动工具栏）

### P5 - 整体打磨
- QSS 主题美化（4 套主题：Light/Dark/Sepia/Green）
- SVG 矢量图标（13 个图标）
- 键盘快捷键完善（Ctrl+1/2/3/4 切换主题，Home/End 首尾页等）
- 窗口状态记忆（分割器布局、上次打开的图书自动恢复）

### P5.1 - Windows EXE 打包
- PyInstaller 打包（onedir 模式）
- 应用图标（blue book SVG → 混合 DIB/PNG ICO → 嵌入 EXE）
- 安装脚本（复制到 LocalAppData、创建快捷方式、注册 .epub 文件关联）

### P6 - 大文件性能优化
- EPUB 懒加载章节（初始化 11.6s → 0.97s）
- HTML 预处理合并冗余 span（DOM 减少 67.8%）
- 正则替代 BeautifulSoup 解析（_extract_body_content 10.3s → 0.017s）
- getClientRects() 行级分页 + clipPath: inset() 精确裁剪
- 阅读进度保存防抖（2 秒 QTimer，关闭时立即 flush）

### P7 - 书库搜索与无限滚动
- 图书搜索框（工具栏 QLineEdit，按书名关键字搜索，大小写不敏感）
- BookRepository.search_by_title() SQL LIKE 查询
- 无限滚动加载（滚动到底部自动加载下一批，每批 30 本）

### 测试
- 113 个单元测试全部通过
- 核心模块覆盖率 ≥ 80%
