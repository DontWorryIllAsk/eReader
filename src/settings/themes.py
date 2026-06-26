APP_THEME_LIGHT = """
QMainWindow {
    background-color: #FAFAFA;
}
QMenuBar {
    background-color: #F0F0F0;
    border-bottom: 1px solid #DDD;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #D0D0D0;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #CCC;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #E3F2FD;
    color: #1565C0;
}
QMenu::separator {
    height: 1px;
    background: #E0E0E0;
    margin: 4px 8px;
}
QToolBar {
    background-color: #F5F5F5;
    border-bottom: 1px solid #DDD;
    padding: 2px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    padding: 5px 10px;
    border-radius: 4px;
    color: #333;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background-color: #E0E0E0;
}
QToolBar QToolButton:pressed {
    background-color: #CCCCCC;
}
QToolBar::separator {
    width: 1px;
    background: #DDD;
    margin: 4px 4px;
}
QSplitter::handle {
    background: #DDD;
    width: 2px;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #DDD;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #333;
}
QComboBox {
    border: 1px solid #CCC;
    border-radius: 4px;
    padding: 4px 8px;
    background: #FFF;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #2196F3;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #CCC;
    border-radius: 4px;
    background: #FFF;
    selection-background-color: #E3F2FD;
    selection-color: #1565C0;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #DDD;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #2196F3;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #1976D2;
}
QSlider::sub-page:horizontal {
    background: #2196F3;
    border-radius: 3px;
}
QLabel {
    color: #333;
}
QPushButton {
    border: 1px solid #CCC;
    border-radius: 4px;
    padding: 5px 12px;
    background: #FFF;
    color: #333;
    font-size: 12px;
}
QPushButton:hover {
    background: #F0F0F0;
    border-color: #BBB;
}
QPushButton:pressed {
    background: #E0E0E0;
}
QListWidget {
    border: 1px solid #DDD;
    border-radius: 4px;
    background: #FFF;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #F0F0F0;
}
QListWidget::item:hover {
    background: #F5F5F5;
}
QListWidget::item:selected {
    background: #E3F2FD;
    color: #1565C0;
}
QScrollArea {
    border: none;
    background: #F5F5F5;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #CCC;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #BBB;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #CCC;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #BBB;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QMessageBox {
    background: #FFF;
}
"""

APP_THEME_DARK = """
QMainWindow {
    background-color: #1E1E1E;
}
QMenuBar {
    background-color: #2D2D2D;
    border-bottom: 1px solid #3D3D3D;
    padding: 2px;
    color: #D4D4D4;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #3D3D3D;
}
QMenu {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
    border-radius: 6px;
    padding: 4px;
    color: #D4D4D4;
}
QMenu::item {
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #094771;
    color: #FFFFFF;
}
QMenu::separator {
    height: 1px;
    background: #3D3D3D;
    margin: 4px 8px;
}
QToolBar {
    background-color: #252526;
    border-bottom: 1px solid #3D3D3D;
    padding: 2px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    padding: 5px 10px;
    border-radius: 4px;
    color: #CCCCCC;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background-color: #3D3D3D;
}
QToolBar QToolButton:pressed {
    background-color: #505050;
}
QToolBar::separator {
    width: 1px;
    background: #3D3D3D;
    margin: 4px 4px;
}
QSplitter::handle {
    background: #3D3D3D;
    width: 2px;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #3D3D3D;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    color: #D4D4D4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #D4D4D4;
}
QComboBox {
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    padding: 4px 8px;
    background: #2D2D2D;
    color: #D4D4D4;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #2196F3;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    background: #2D2D2D;
    color: #D4D4D4;
    selection-background-color: #094771;
    selection-color: #FFFFFF;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #3D3D3D;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #2196F3;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #1976D2;
}
QSlider::sub-page:horizontal {
    background: #2196F3;
    border-radius: 3px;
}
QLabel {
    color: #D4D4D4;
}
QPushButton {
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    padding: 5px 12px;
    background: #2D2D2D;
    color: #D4D4D4;
    font-size: 12px;
}
QPushButton:hover {
    background: #3D3D3D;
    border-color: #555;
}
QPushButton:pressed {
    background: #505050;
}
QListWidget {
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    background: #252526;
    color: #D4D4D4;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #333;
}
QListWidget::item:hover {
    background: #2D2D2D;
}
QListWidget::item:selected {
    background: #094771;
    color: #FFFFFF;
}
QScrollArea {
    border: none;
    background: #1E1E1E;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #555;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #555;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #666;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QMessageBox {
    background: #2D2D2D;
}
"""

APP_THEME_SEPIA = """
QMainWindow {
    background-color: #F4ECD8;
}
QMenuBar {
    background-color: #EDE3CC;
    border-bottom: 1px solid #D4C9AE;
    padding: 2px;
    color: #2E2E2E;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #D4C9AE;
}
QMenu {
    background-color: #F4ECD8;
    border: 1px solid #D4C9AE;
    border-radius: 6px;
    padding: 4px;
    color: #2E2E2E;
}
QMenu::item {
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #E3D5B8;
    color: #2E2E2E;
}
QMenu::separator {
    height: 1px;
    background: #D4C9AE;
    margin: 4px 8px;
}
QToolBar {
    background-color: #EDE3CC;
    border-bottom: 1px solid #D4C9AE;
    padding: 2px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    padding: 5px 10px;
    border-radius: 4px;
    color: #2E2E2E;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background-color: #D4C9AE;
}
QToolBar QToolButton:pressed {
    background-color: #C4B99E;
}
QToolBar::separator {
    width: 1px;
    background: #D4C9AE;
    margin: 4px 4px;
}
QSplitter::handle {
    background: #D4C9AE;
    width: 2px;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #D4C9AE;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    color: #2E2E2E;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #2E2E2E;
}
QComboBox {
    border: 1px solid #D4C9AE;
    border-radius: 4px;
    padding: 4px 8px;
    background: #F4ECD8;
    color: #2E2E2E;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #B8860B;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #D4C9AE;
    border-radius: 4px;
    background: #F4ECD8;
    color: #2E2E2E;
    selection-background-color: #E3D5B8;
    selection-color: #2E2E2E;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #D4C9AE;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #B8860B;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #996F0A;
}
QSlider::sub-page:horizontal {
    background: #B8860B;
    border-radius: 3px;
}
QLabel {
    color: #2E2E2E;
}
QPushButton {
    border: 1px solid #D4C9AE;
    border-radius: 4px;
    padding: 5px 12px;
    background: #F4ECD8;
    color: #2E2E2E;
    font-size: 12px;
}
QPushButton:hover {
    background: #EDE3CC;
    border-color: #B8860B;
}
QPushButton:pressed {
    background: #D4C9AE;
}
QListWidget {
    border: 1px solid #D4C9AE;
    border-radius: 4px;
    background: #F4ECD8;
    color: #2E2E2E;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #EDE3CC;
}
QListWidget::item:hover {
    background: #EDE3CC;
}
QListWidget::item:selected {
    background: #E3D5B8;
    color: #2E2E2E;
}
QScrollArea {
    border: none;
    background: #EDE3CC;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #D4C9AE;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #C4B99E;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #D4C9AE;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #C4B99E;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QMessageBox {
    background: #F4ECD8;
}
"""

APP_THEME_GREEN = """
QMainWindow {
    background-color: #C7EDCC;
}
QMenuBar {
    background-color: #B5E0BB;
    border-bottom: 1px solid #9BD4A3;
    padding: 2px;
    color: #2E5E34;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #9BD4A3;
}
QMenu {
    background-color: #C7EDCC;
    border: 1px solid #9BD4A3;
    border-radius: 6px;
    padding: 4px;
    color: #2E5E34;
}
QMenu::item {
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #A8DFAF;
    color: #2E5E34;
}
QMenu::separator {
    height: 1px;
    background: #9BD4A3;
    margin: 4px 8px;
}
QToolBar {
    background-color: #B5E0BB;
    border-bottom: 1px solid #9BD4A3;
    padding: 2px 6px;
    spacing: 4px;
}
QToolBar QToolButton {
    padding: 5px 10px;
    border-radius: 4px;
    color: #2E5E34;
    font-size: 13px;
}
QToolBar QToolButton:hover {
    background-color: #9BD4A3;
}
QToolBar QToolButton:pressed {
    background-color: #8BC893;
}
QToolBar::separator {
    width: 1px;
    background: #9BD4A3;
    margin: 4px 4px;
}
QSplitter::handle {
    background: #9BD4A3;
    width: 2px;
}
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #9BD4A3;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    color: #2E5E34;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #2E5E34;
}
QComboBox {
    border: 1px solid #9BD4A3;
    border-radius: 4px;
    padding: 4px 8px;
    background: #C7EDCC;
    color: #2E5E34;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #4CAF50;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #9BD4A3;
    border-radius: 4px;
    background: #C7EDCC;
    color: #2E5E34;
    selection-background-color: #A8DFAF;
    selection-color: #2E5E34;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #9BD4A3;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background: #4CAF50;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #388E3C;
}
QSlider::sub-page:horizontal {
    background: #4CAF50;
    border-radius: 3px;
}
QLabel {
    color: #2E5E34;
}
QPushButton {
    border: 1px solid #9BD4A3;
    border-radius: 4px;
    padding: 5px 12px;
    background: #C7EDCC;
    color: #2E5E34;
    font-size: 12px;
}
QPushButton:hover {
    background: #B5E0BB;
    border-color: #4CAF50;
}
QPushButton:pressed {
    background: #9BD4A3;
}
QListWidget {
    border: 1px solid #9BD4A3;
    border-radius: 4px;
    background: #C7EDCC;
    color: #2E5E34;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #B5E0BB;
}
QListWidget::item:hover {
    background: #B5E0BB;
}
QListWidget::item:selected {
    background: #A8DFAF;
    color: #2E5E34;
}
QScrollArea {
    border: none;
    background: #B5E0BB;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #9BD4A3;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #8BC893;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #9BD4A3;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #8BC893;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
QMessageBox {
    background: #C7EDCC;
}
"""

APP_THEMES = {
    "light": APP_THEME_LIGHT,
    "dark": APP_THEME_DARK,
    "sepia": APP_THEME_SEPIA,
    "green": APP_THEME_GREEN,
}
