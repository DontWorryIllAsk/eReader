import json
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QUrl
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.readers.epub_reader import Chapter, EpubReader
from src.settings.settings import ReaderSettings, ThemeMode
from src.icons import get_icon


CHAPTER_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; }}
html, body {{
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
    background-color: {bg_color};
}}
#viewport {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: relative;
    background-color: {bg_color};
}}
#reader-content {{
    font-family: {font_family};
    font-size: {font_size}px;
    line-height: 1.8;
    padding: 1em 2em;
    background-color: {bg_color};
    color: {text_color};
    max-width: 800px;
    margin: 0 auto;
    opacity: 0;
}}
#reader-content img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}}
#reader-content a {{
    color: inherit;
}}
.ann-highlight {{
    background-color: #FFFF00;
    padding: 1px 0;
    border-radius: 2px;
    cursor: pointer;
}}
.ann-underline {{
    text-decoration: underline;
    text-decoration-color: #FF0000;
    text-underline-offset: 3px;
    cursor: pointer;
}}
.ann-strikethrough {{
    text-decoration: line-through;
    text-decoration-color: #FF0000;
    cursor: pointer;
}}
.ann-highlight:hover {{
    background-color: #FFEB3B;
}}
.ann-underline:hover {{
    background-color: rgba(255, 0, 0, 0.08);
}}
.ann-strikethrough:hover {{
    background-color: rgba(255, 0, 0, 0.08);
}}
</style>
</head>
<body>
<div id="viewport">
<div id="reader-content">
{content}
</div>
</div>
<script>
document.title = '';
var currentPage = 0;
var pageBreaks = [];
var paginationReady = false;

function computePageBreaks() {{
    var viewport = document.getElementById('viewport');
    var content = document.getElementById('reader-content');
    if (!viewport || !content) return false;

    var vh = viewport.clientHeight;
    if (vh <= 0) return false;

    content.style.transform = 'translateY(0px)';

    pageBreaks = [0];
    var contentRect = content.getBoundingClientRect();
    var contentStyle = getComputedStyle(content);
    var paddingTop = parseFloat(contentStyle.paddingTop) || 0;
    var contentTop = contentRect.top;

    var items = [];
    var images = content.getElementsByTagName('img');
    for (var i = 0; i < images.length; i++) {{
        var img = images[i];
        var rect = img.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {{
            items.push({{
                top: rect.top - contentTop,
                bottom: rect.bottom - contentTop,
                isImage: true
            }});
        }}
    }}

    var range = document.createRange();
    range.selectNodeContents(content);
    var rects = range.getClientRects();
    for (var i = 0; i < rects.length; i++) {{
        var r = rects[i];
        if (r.width > 0 && r.height > 0 && r.height < vh) {{
            items.push({{
                top: r.top - contentTop,
                bottom: r.bottom - contentTop,
                isImage: false
            }});
        }}
    }}

    if (items.length === 0) {{
        var totalH = content.scrollHeight;
        var numPages = Math.max(1, Math.ceil(totalH / vh));
        for (var i = 1; i < numPages; i++) {{
            pageBreaks.push(i * vh);
        }}
        return true;
    }}

    items.sort(function(a, b) {{ return a.top - b.top || a.bottom - b.bottom; }});

    var deduped = [];
    for (var i = 0; i < items.length; i++) {{
        if (i === 0 || items[i].top !== items[i-1].top || items[i].bottom !== items[i-1].bottom || items[i].isImage !== items[i-1].isImage) {{
            var isDup = false;
            for (var j = deduped.length - 1; j >= 0; j--) {{
                if (deduped[j].top === items[i].top && deduped[j].bottom === items[i].bottom) {{
                    if (items[i].isImage) deduped[j].isImage = true;
                    isDup = true;
                    break;
                }}
                if (deduped[j].bottom < items[i].top) break;
            }}
            if (!isDup) deduped.push(items[i]);
        }}
    }}

    if (deduped.length === 0) {{
        pageBreaks = [0];
        return true;
    }}

    var currentBreak = 0;
    var i = 0;

    while (i < deduped.length) {{
        var item = deduped[i];
        var pageBottom = currentBreak + vh;

        if (item.bottom <= pageBottom) {{
            i++;
            continue;
        }}

        var nearPageStart = (item.top - currentBreak) <= paddingTop + 2;

        if (item.isImage) {{
            if (nearPageStart) {{
                while (item.bottom > currentBreak + vh) {{
                    currentBreak += vh;
                    pageBreaks.push(currentBreak);
                }}
            }} else if (item.top >= pageBottom) {{
                pageBreaks.push(item.top);
                currentBreak = item.top;
                if (item.bottom - item.top > vh) {{
                    while (item.bottom > currentBreak + vh) {{
                        currentBreak += vh;
                        pageBreaks.push(currentBreak);
                    }}
                }}
            }} else {{
                pageBreaks.push(item.top);
                currentBreak = item.top;
                if (item.bottom - item.top > vh) {{
                    while (item.bottom > currentBreak + vh) {{
                        currentBreak += vh;
                        pageBreaks.push(currentBreak);
                    }}
                }}
            }}
        }} else {{
            if (item.top >= pageBottom) {{
                pageBreaks.push(item.top);
                currentBreak = item.top;
            }} else if (nearPageStart) {{
                currentBreak += vh;
                pageBreaks.push(currentBreak);
            }} else if (item.top > currentBreak) {{
                pageBreaks.push(item.top);
                currentBreak = item.top;
            }} else {{
                currentBreak += vh;
                pageBreaks.push(currentBreak);
            }}
        }}
        i++;
    }}

    return true;
}}

function showPage(page) {{
    if (page < 0) page = 0;
    if (page >= pageBreaks.length) page = pageBreaks.length - 1;
    currentPage = page;
    var content = document.getElementById('reader-content');
    var viewport = document.getElementById('viewport');
    var offset = pageBreaks[page];
    var vh = viewport.clientHeight;
    var visibleBottom;
    if (page + 1 < pageBreaks.length) {{
        visibleBottom = Math.min(pageBreaks[page + 1], offset + vh);
    }} else {{
        visibleBottom = offset + vh;
    }}
    var totalHeight = content.scrollHeight;
    var bottomClip = totalHeight - visibleBottom;
    if (bottomClip < 0) bottomClip = 0;
    content.style.transform = 'translateY(-' + offset + 'px)';
    content.style.clipPath = 'inset(' + offset + 'px 0 ' + bottomClip + 'px 0)';
    content.style.opacity = '1';
    document.title = (currentPage + 1) + '/' + pageBreaks.length;
}}

function nextPage() {{
    if (!paginationReady) return;
    if (currentPage >= pageBreaks.length - 1) {{
        document.title = 'NEXT_CHAPTER';
    }} else {{
        showPage(currentPage + 1);
    }}
}}

function prevPage() {{
    if (!paginationReady) return;
    if (currentPage <= 0) {{
        document.title = 'PREV_CHAPTER';
    }} else {{
        showPage(currentPage - 1);
    }}
}}

function initPagination() {{
    var viewport = document.getElementById('viewport');
    if (!viewport || viewport.clientHeight <= 0) {{
        setTimeout(initPagination, 100);
        return;
    }}
    var content = document.getElementById('reader-content');
    var images = content ? content.getElementsByTagName('img') : [];
    var pending = 0;
    for (var i = 0; i < images.length; i++) {{
        if (!images[i].complete) pending++;
    }}
    if (pending > 0) {{
        var handler = function() {{
            pending--;
            if (pending <= 0) {{
                setTimeout(function() {{
                    if (computePageBreaks()) {{
                        paginationReady = true;
                        showPage(0);
                    }}
                }}, 100);
            }}
        }};
        for (var i = 0; i < images.length; i++) {{
            if (!images[i].complete) {{
                images[i].addEventListener('load', handler);
                images[i].addEventListener('error', handler);
            }}
        }}
        setTimeout(function() {{
            if (!paginationReady) {{
                if (computePageBreaks()) {{
                    paginationReady = true;
                    showPage(0);
                }}
            }}
        }}, 3000);
    }} else {{
        if (computePageBreaks()) {{
            paginationReady = true;
            showPage(0);
        }} else {{
            setTimeout(initPagination, 100);
        }}
    }}
}}

var _resizeTimer = null;
var _resizeSavedOffset = 0;

window.onresize = function() {{
    var viewport = document.getElementById('viewport');
    if (!viewport || viewport.clientHeight <= 0) return;
    if (paginationReady && pageBreaks.length > 0) {{
        _resizeSavedOffset = pageBreaks[currentPage];
    }}
    paginationReady = false;
    if (_resizeTimer) clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(function() {{
        _resizeTimer = null;
        if (computePageBreaks() && pageBreaks.length > 0) {{
            paginationReady = true;
            var best = 0;
            for (var i = 0; i < pageBreaks.length; i++) {{
                if (Math.abs(pageBreaks[i] - _resizeSavedOffset) < Math.abs(pageBreaks[best] - _resizeSavedOffset)) best = i;
            }}
            showPage(best);
        }}
    }}, 200);
}};

var annotations = [];
var nextAnnId = 1;

function getSelectedTextInfo() {{
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return null;
    var range = sel.getRangeAt(0);
    var content = document.getElementById('reader-content');
    if (!content) return null;
    if (!content.contains(range.startContainer) || !content.contains(range.endContainer)) return null;
    var text = sel.toString().trim();
    if (!text) return null;
    var preRange = document.createRange();
    preRange.selectNodeContents(content);
    preRange.setEnd(range.startContainer, range.startOffset);
    var startOffset = preRange.toString().length;
    var endOffset = startOffset + text.length;
    return {{ text: text, startOffset: startOffset, endOffset: endOffset }};
}}

function applyAnnotation(annId, annType, startOffset, endOffset, color) {{
    var content = document.getElementById('reader-content');
    if (!content) return false;
    var textNodes = [];
    var walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null);
    var node;
    while (node = walker.nextNode()) {{
        textNodes.push(node);
    }}
    var charIndex = 0;
    var started = false;
    for (var i = 0; i < textNodes.length; i++) {{
        var tn = textNodes[i];
        var nodeLen = tn.textContent.length;
        var nodeStart = charIndex;
        var nodeEnd = charIndex + nodeLen;
        if (nodeEnd <= startOffset) {{
            charIndex = nodeEnd;
            continue;
        }}
        if (nodeStart >= endOffset) break;
        var overlapStart = Math.max(startOffset, nodeStart);
        var overlapEnd = Math.min(endOffset, nodeEnd);
        if (overlapStart >= overlapEnd) {{
            charIndex = nodeEnd;
            continue;
        }}
        var relStart = overlapStart - nodeStart;
        var relEnd = overlapEnd - nodeStart;
        var before = tn.textContent.substring(0, relStart);
        var middle = tn.textContent.substring(relStart, relEnd);
        var after = tn.textContent.substring(relEnd);
        var span = document.createElement('span');
        span.className = 'ann-' + annType;
        span.setAttribute('data-ann-id', annId);
        if (color) span.style.backgroundColor = color;
        span.textContent = middle;
        var parent = tn.parentNode;
        if (after) {{
            var afterNode = document.createTextNode(after);
            parent.insertBefore(afterNode, tn.nextSibling);
            parent.insertBefore(span, afterNode);
        }} else {{
            parent.insertBefore(span, tn.nextSibling);
        }}
        if (before) {{
            tn.textContent = before;
        }} else {{
            parent.removeChild(tn);
        }}
        charIndex = nodeEnd;
    }}
    return true;
}}

function removeAnnotation(annId) {{
    var content = document.getElementById('reader-content');
    if (!content) return;
    var spans = content.querySelectorAll('span[data-ann-id="' + annId + '"]');
    for (var i = spans.length - 1; i >= 0; i--) {{
        var span = spans[i];
        var parent = span.parentNode;
        while (span.firstChild) {{
            parent.insertBefore(span.firstChild, span);
        }}
        parent.removeChild(span);
        parent.normalize();
    }}
}}

function loadAnnotations(annList) {{
    for (var i = 0; i < annList.length; i++) {{
        var a = annList[i];
        applyAnnotation(a.id, a.annotation_type, a.start_offset, a.end_offset, a.color || '');
    }}
    annotations = annList;
    if (annotations.length > 0) {{
        nextAnnId = Math.max.apply(null, annotations.map(function(a) {{ return a.id; }})) + 1;
    }}
}}

function clearAnnotations() {{
    var content = document.getElementById('reader-content');
    if (!content) return;
    var spans = content.querySelectorAll('span[data-ann-id]');
    for (var i = spans.length - 1; i >= 0; i--) {{
        var span = spans[i];
        var parent = span.parentNode;
        while (span.firstChild) {{
            parent.insertBefore(span.firstChild, span);
        }}
        parent.removeChild(span);
        parent.normalize();
    }}
    annotations = [];
    nextAnnId = 1;
}}

document.addEventListener('mouseup', function(e) {{
    var sel = window.getSelection();
    if (sel && !sel.isCollapsed && sel.toString().trim().length > 0) {{
        var info = getSelectedTextInfo();
        if (info) {{
            document.title = 'TEXT_SELECTED:' + JSON.stringify(info);
        }}
    }}
}});

document.addEventListener('click', function(e) {{
    var target = e.target;
    if (target && target.hasAttribute && target.hasAttribute('data-ann-id')) {{
        var annId = target.getAttribute('data-ann-id');
        document.title = 'ANN_CLICKED:' + annId;
    }}
}});

document.addEventListener('keydown', function(e) {{
    if (!paginationReady) return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') {{
        e.preventDefault();
        nextPage();
    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        e.preventDefault();
        prevPage();
    }} else if (e.key === 'Home') {{
        e.preventDefault();
        showPage(0);
    }} else if (e.key === 'End') {{
        e.preventDefault();
        if (pageBreaks.length > 0) showPage(pageBreaks.length - 1);
    }}
}});

document.addEventListener('click', function(e) {{
    var target = e.target;
    while (target && target.tagName !== 'A') {{
        target = target.parentElement;
    }}
    if (target && target.getAttribute('href')) {{
        var href = target.getAttribute('href');
        if (href && !href.startsWith('http') && !href.startsWith('data:')) {{
            e.preventDefault();
            document.title = 'LINK_CLICKED:' + href;
        }}
    }}
}});
</script>
</body>
</html>"""


class _ReaderWebView(QWebEngineView):
    """Custom QWebEngineView that forwards Escape/F11 keys to parent."""

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            event.ignore()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            event.ignore()
            return
        super().keyReleaseEvent(event)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)


class ReaderWidget(QWidget):
    """Main EPUB reader widget with WebEngine-based rendering and pagination."""

    chapter_changed = Signal(int)
    exit_fullscreen_requested = Signal()
    reading_progress_changed = Signal(int, float)
    text_selected = Signal(str, int, int)
    annotation_clicked = Signal(int)

    link_clicked = Signal(str)

    def __init__(self, settings: ReaderSettings | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._epub_reader: Optional[EpubReader] = None
        self._current_chapter_index: int = 0
        self._settings = settings if settings is not None else ReaderSettings()
        self._book_file_path: str = ""
        self._fullscreen_mode = False
        self._toolbar_auto_hidden = False
        self._pending_position: float = 0.0
        self._pending_annotations: list[dict] = []
        self._closing = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the UI components."""
        self.setMouseTracking(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        self._web_view = _ReaderWebView()
        self._web_view.page().titleChanged.connect(self._on_title_changed)
        self._web_view.page().loadFinished.connect(self._on_load_finished)
        self._web_view.installEventFilter(self)
        layout.addWidget(self._web_view, 1)

        self._web_view.setHtml(
            "<html><body style='margin:0;background-color:white;'></body>"
            "<script>function initPagination(){} function computePageBreaks(){return true}"
            " function showPage(){} function nextPage(){} function prevPage(){}"
            " function getSelectedTextInfo(){return null} function applyAnnotation(){return false}"
            " function removeAnnotation(){} function loadAnnotations(){} function clearAnnotations(){}"
            " var currentPage=0; var pageBreaks=[0]; var paginationReady=false;"
            " var annotations=[]; var nextAnnId=1;"
            " document.title='';</script></html>"
        )

    def _create_toolbar(self) -> QToolBar:
        """Create a compact reader toolbar."""
        toolbar = QToolBar("Reader Toolbar")
        toolbar.setMovable(False)

        prev_action = QAction(get_icon("prev-chapter"), "< Prev", self)
        prev_action.triggered.connect(self.prev_page)
        toolbar.addAction(prev_action)

        self._page_label = QLabel("0 / 0")
        self._page_label.setMinimumWidth(60)
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self._page_label)

        next_action = QAction(get_icon("next-chapter"), "Next >", self)
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        self._chapter_combo = QComboBox()
        self._chapter_combo.setMinimumWidth(200)
        self._chapter_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self._chapter_combo.currentIndexChanged.connect(self._on_chapter_selected)
        toolbar.addWidget(self._chapter_combo)

        toolbar.addSeparator()

        self._book_info_label = QLabel("")
        toolbar.addWidget(self._book_info_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._exit_fullscreen_action = QAction(get_icon("exit-fullscreen"), "Exit Fullscreen", self)
        self._exit_fullscreen_action.setVisible(False)
        self._exit_fullscreen_action.triggered.connect(self._request_exit_fullscreen)
        toolbar.addAction(self._exit_fullscreen_action)

        return toolbar

    def load_book(self, file_path: str | Path, chapter_index: int = 0, position_in_chapter: float = 0.0) -> None:
        """Load an EPUB book for reading."""
        try:
            self._epub_reader = EpubReader(file_path)
            self._book_file_path = str(file_path)
            self._populate_chapter_combo()
            self._current_chapter_index = 0
            self._pending_position = position_in_chapter
            self._display_chapter(chapter_index)
            if self._epub_reader:
                self._book_info_label.setText(
                    f"{self._epub_reader.title} — {self._epub_reader.author}"
                )
        except (FileNotFoundError, ValueError) as e:
            self._web_view.setHtml(f"<h2>Error loading book</h2><p>{e}</p>")

    def _populate_chapter_combo(self) -> None:
        """Fill the chapter dropdown with chapter titles."""
        self._chapter_combo.blockSignals(True)
        self._chapter_combo.clear()
        if self._epub_reader:
            for chapter in self._epub_reader.chapters:
                title = chapter.title if chapter.title else f"Chapter {chapter.index + 1}"
                self._chapter_combo.addItem(title)
        self._chapter_combo.blockSignals(False)

    def _display_chapter(self, index: int) -> None:
        """Render a chapter in the web view with pagination."""
        if self._epub_reader is None:
            return
        chapter = self._epub_reader.get_chapter(index)
        if chapter is None:
            return

        soup_content = self._extract_body_content(chapter.html_content)

        html = CHAPTER_HTML_TEMPLATE.format(
            font_family=self._settings.font_family,
            font_size=self._settings.font_size,
            bg_color=self._settings.get_bg_color(),
            text_color=self._settings.get_text_color(),
            content=soup_content,
        )

        self._current_chapter_index = index
        self._chapter_combo.setCurrentIndex(index)

        base_url = QUrl.fromLocalFile(self._book_file_path)
        self._web_view.setHtml(html, base_url)

        QTimer.singleShot(500, lambda: self._web_view.page().runJavaScript(
            "if (!paginationReady) { initPagination(); }"
        ))

    _BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.IGNORECASE | re.DOTALL)

    _BOOKSPAN_RE = re.compile(
        r"<span\s+xmlns=[^\s>]+\s+class=['\"]bookspan['\"]\s+id=['\"][^'\"]*['\"]>(.*?)</span>",
        re.DOTALL,
    )
    _LINE_SPAN_RE = re.compile(
        r"<span\s+id=['\"][^'\"]*['\"]>(.*?)</span>",
        re.DOTALL,
    )

    def _extract_body_content(self, html: str) -> str:
        """Extract the inner content from chapter HTML body and resolve images."""
        m = self._BODY_RE.search(html)
        content = m.group(1) if m else html

        content = self._BOOKSPAN_RE.sub(r"\1", content)
        content = self._LINE_SPAN_RE.sub(r"\1", content)

        if self._epub_reader:
            content = self._epub_reader.resolve_images(content)

        return content

    @Slot(bool)
    def _on_load_finished(self, ok: bool) -> None:
        """Initialize pagination after page finishes loading."""
        if self._closing:
            return
        if ok and self._epub_reader is not None:
            pos = self._pending_position
            self._pending_position = 0.0
            if pos > 0:
                js = (
                    f"initPagination(); setTimeout(function() {{"
                    f" if (paginationReady && pageBreaks.length > 0) {{"
                    f" var p = Math.min(Math.floor({pos} * pageBreaks.length), pageBreaks.length - 1);"
                    f" showPage(p);"
                    f" }} }}, 300);"
                )
            else:
                js = "initPagination();"
            QTimer.singleShot(200, lambda: self._web_view.page().runJavaScript(js))
            self._load_pending_annotations()

    def _on_title_changed(self, title: str) -> None:
        """Handle title changes: page info, chapter navigation, or annotation events."""
        if self._closing:
            return
        if not title or not isinstance(title, str):
            return
        try:
            if title == "NEXT_CHAPTER":
                self.next_chapter()
                return
            if title == "PREV_CHAPTER":
                self.prev_chapter()
                return
            if title.startswith("TEXT_SELECTED:"):
                info = json.loads(title[len("TEXT_SELECTED:"):])
                self.text_selected.emit(
                    info.get("text", ""),
                    info.get("startOffset", 0),
                    info.get("endOffset", 0),
                )
                self._web_view.page().runJavaScript("document.title = '';")
                return
            if title.startswith("ANN_CLICKED:"):
                ann_id = int(title[len("ANN_CLICKED:"):])
                self.annotation_clicked.emit(ann_id)
                self._web_view.page().runJavaScript("document.title = '';")
                return
            if title.startswith("LINK_CLICKED:"):
                href = title[len("LINK_CLICKED:"):]
                self.link_clicked.emit(href)
                self._web_view.page().runJavaScript("document.title = '';")
                return
            if re.match(r"^\d+/\d+$", title):
                self._page_label.setText(title)
                parts = title.split("/")
                if len(parts) == 2:
                    current = int(parts[0]) - 1
                    total = int(parts[1])
                    if total > 0:
                        self.reading_progress_changed.emit(
                            self._current_chapter_index, current / total
                        )
        except (RuntimeError, json.JSONDecodeError, ValueError, KeyError):
            pass

    @Slot()
    def next_page(self) -> None:
        """Go to next page within chapter, or next chapter at end."""
        self._web_view.page().runJavaScript("nextPage();")

    @Slot()
    def prev_page(self) -> None:
        """Go to previous page within chapter, or previous chapter at start."""
        self._web_view.page().runJavaScript("prevPage();")

    @Slot()
    def next_chapter(self) -> None:
        """Navigate to the next chapter."""
        if self._epub_reader and self._current_chapter_index < self._epub_reader.total_chapters - 1:
            self._display_chapter(self._current_chapter_index + 1)
            self.chapter_changed.emit(self._current_chapter_index)

    @Slot()
    def prev_chapter(self) -> None:
        """Navigate to the previous chapter."""
        if self._epub_reader and self._current_chapter_index > 0:
            self._display_chapter(self._current_chapter_index - 1)
            self.chapter_changed.emit(self._current_chapter_index)

    @Slot(int)
    def _on_chapter_selected(self, index: int) -> None:
        """Handle chapter selection from dropdown."""
        if index >= 0 and index != self._current_chapter_index:
            self._display_chapter(index)
            self.chapter_changed.emit(index)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard navigation."""
        if event.key() == Qt.Key.Key_Escape and self._fullscreen_mode:
            self._request_exit_fullscreen()
            return
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            self.next_page()
        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self.prev_page()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        """Catch Escape/F11 from the web view before Chromium consumes them."""
        if obj is self._web_view and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape and self._fullscreen_mode:
                self._request_exit_fullscreen()
                return True
            if event.key() == Qt.Key.Key_F11:
                return True
        return super().eventFilter(obj, event)

    def set_fullscreen_mode(self, enabled: bool) -> None:
        """Enable or disable fullscreen reading mode."""
        self._fullscreen_mode = enabled
        self._exit_fullscreen_action.setVisible(enabled)
        if enabled:
            self._toolbar.hide()
            self._toolbar_auto_hidden = True
        else:
            self._toolbar.show()
            self._toolbar_auto_hidden = False

    def _request_exit_fullscreen(self) -> None:
        """Request the main window to exit fullscreen mode."""
        self.exit_fullscreen_requested.emit()

    def mouseMoveEvent(self, event) -> None:
        """Show toolbar on mouse hover at top in fullscreen mode."""
        if not self._fullscreen_mode:
            super().mouseMoveEvent(event)
            return
        toolbar_height = self._toolbar.height()
        if toolbar_height == 0:
            toolbar_height = 36
        if event.position().y() <= toolbar_height + 4:
            if self._toolbar_auto_hidden:
                self._toolbar.show()
                self._toolbar_auto_hidden = False
        else:
            if not self._toolbar_auto_hidden:
                self._toolbar.hide()
                self._toolbar_auto_hidden = True

    def apply_settings(self, settings: ReaderSettings) -> None:
        """Apply new reader settings and re-render."""
        self._settings = settings
        if self._epub_reader:
            self._display_chapter(self._current_chapter_index)

    def resizeEvent(self, event) -> None:
        """Re-paginate on resize."""
        super().resizeEvent(event)
        if self._closing:
            return

    @property
    def current_chapter_index(self) -> int:
        """Current chapter index."""
        return self._current_chapter_index

    @property
    def epub_reader(self) -> Optional[EpubReader]:
        """Current EPUB reader instance."""
        return self._epub_reader

    def get_current_progress(self) -> tuple[int, float]:
        """Get current reading progress as (chapter_index, position_in_chapter)."""
        return self._current_chapter_index, self._get_page_position()

    def _get_page_position(self) -> float:
        """Get current page position as a fraction within the chapter."""
        label = self._page_label.text()
        match = re.match(r"^(\d+)/(\d+)$", label)
        if match:
            current = int(match.group(1)) - 1
            total = int(match.group(2))
            if total > 0:
                return current / total
        return 0.0

    def apply_annotation(self, ann_id: int, ann_type: str, start_offset: int, end_offset: int, color: str = "") -> None:
        """Apply an annotation highlight/underline/strikethrough in the current page."""
        js = f"applyAnnotation({ann_id}, '{ann_type}', {start_offset}, {end_offset}, '{color}');"
        self._web_view.page().runJavaScript(js)

    def remove_annotation(self, ann_id: int) -> None:
        """Remove an annotation from the current page."""
        js = f"removeAnnotation({ann_id});"
        self._web_view.page().runJavaScript(js)

    def set_pending_annotations(self, annotations: list[dict]) -> None:
        """Set annotations to be loaded after the next chapter display."""
        self._pending_annotations = annotations

    def _load_pending_annotations(self) -> None:
        """Load pending annotations into the current chapter after pagination."""
        if not self._pending_annotations:
            return
        ann_list = json.dumps(self._pending_annotations)
        js = f"loadAnnotations({ann_list});"
        QTimer.singleShot(600, lambda: self._web_view.page().runJavaScript(js))
        self._pending_annotations = []
