import base64
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ebooklib import epub


@dataclass
class Chapter:
    """Represents a single chapter in an EPUB book."""

    index: int
    title: str
    html_content: str = ""
    raw_content: bytes = b""

    _item_id: str = ""
    _item_name: str = ""
    _loaded: bool = True

    def ensure_loaded(self, book) -> None:
        if self._loaded:
            return
        item = book.get_item_with_id(self._item_id)
        if item is not None:
            raw = item.get_content()
            self.raw_content = raw
            self.html_content = raw.decode("utf-8", errors="replace")
        self._loaded = True


ITEM_DOCUMENT = 9
ITEM_IMAGE = 1
ITEM_COVER = 10

_HEADING_RE = re.compile(r"<(h[1-3])[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_RE = re.compile(r"&\w+;")


class EpubReader:
    """Parses and provides access to EPUB book content."""

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        if not self._file_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {self._file_path}")
        if not self._file_path.suffix.lower() == ".epub":
            raise ValueError(f"Not an EPUB file: {self._file_path}")
        self._book: Optional[epub.EpubBook] = None
        self._chapters: list[Chapter] = []
        self._metadata: dict[str, str] = {}
        self._toc: list[dict[str, object]] = []
        self._image_cache: dict[str, object] = {}
        self._load()

    def _load(self) -> None:
        """Load and parse the EPUB file."""
        self._book = epub.read_epub(str(self._file_path))
        self._extract_metadata()
        self._build_image_cache()
        self._extract_chapters()
        self._extract_toc()

    def _extract_metadata(self) -> None:
        """Extract book metadata (title, author, etc.)."""
        if self._book is None:
            return
        self._metadata["title"] = self._book.get_metadata("DC", "title")[0][0] if self._book.get_metadata("DC", "title") else "Unknown Title"
        self._metadata["author"] = self._book.get_metadata("DC", "creator")[0][0] if self._book.get_metadata("DC", "creator") else "Unknown Author"
        self._metadata["language"] = self._book.get_metadata("DC", "language")[0][0] if self._book.get_metadata("DC", "language") else ""

    def _build_image_cache(self) -> None:
        """Build a lookup cache for image items by name."""
        if self._book is None:
            return
        for item in self._book.get_items():
            if item.get_type() in (ITEM_IMAGE, ITEM_COVER):
                name = item.get_name().replace("\\", "/")
                self._image_cache[name] = item
                if "/" in name:
                    self._image_cache[name.split("/")[-1]] = item

    def _extract_chapters(self) -> None:
        """Extract chapters from the EPUB spine (correct reading order).

        Uses lazy loading: chapter content is only read when accessed,
        not during initial EPUB loading. This makes opening large books
        much faster.
        """
        if self._book is None:
            return
        chapter_index = 0
        for item_id, _linear in self._book.spine:
            item = self._book.get_item_with_id(item_id)
            if item is None or item.get_type() != ITEM_DOCUMENT:
                continue
            title = self._extract_chapter_title_fast(item)
            chapter = Chapter(
                index=chapter_index,
                title=title,
                _item_id=item.get_id(),
                _item_name=item.get_name(),
                _loaded=False,
            )
            self._chapters.append(chapter)
            chapter_index += 1

    def _extract_chapter_title_fast(self, item) -> str:
        """Extract chapter title using TOC first, then regex on HTML head.

        Avoids BeautifulSoup parsing of the entire HTML body which is
        very slow for large chapters (1-2 MB each).
        """
        item_id = item.get_id()

        # Try TOC first (no HTML parsing needed)
        for toc_item in self._book.toc if self._book else []:
            entry = toc_item[0] if isinstance(toc_item, tuple) else toc_item
            href = getattr(entry, "href", "")
            if item_id in href or href.split("#")[0] in (item_id + ".xhtml", item_id):
                return entry.title

        # Read only the beginning of the HTML for title extraction
        raw = item.get_content()
        head_end = raw.find(b"</head>")
        if head_end < 0:
            head_end = min(len(raw), 5000)
        else:
            head_end += 7
        head_html = raw[:head_end].decode("utf-8", errors="replace")

        # Try <title> tag first
        title_match = re.search(r"<title[^>]*>(.*?)</title>", head_html, re.IGNORECASE | re.DOTALL)
        if title_match:
            text = _TAG_RE.sub("", title_match.group(1)).strip()
            if text and len(text) <= 80:
                return text

        # Try heading tags in the beginning of body
        search_size = min(len(raw), 10000)
        search_html = raw[:search_size].decode("utf-8", errors="replace")
        for match in _HEADING_RE.finditer(search_html):
            text = _TAG_RE.sub("", match.group(2)).strip()
            if text and len(text) <= 80:
                return text

        # Fallback to item name
        clean = item.get_name().replace(".xhtml", "").replace(".html", "")
        if "/" in clean:
            clean = clean.split("/")[-1]
        return clean if clean else "Section"

    def _extract_toc(self) -> None:
        """Extract table of contents."""
        if self._book is None:
            return
        for item in self._book.toc:
            if isinstance(item, tuple):
                section, children = item
                child_entries = []
                for c in children:
                    if isinstance(c, tuple):
                        child_entries.append({"title": c[0].title, "href": c[0].href})
                    else:
                        child_entries.append({"title": c.title, "href": c.href})
                self._toc.append({
                    "title": section.title,
                    "href": section.href,
                    "children": child_entries,
                })
            else:
                self._toc.append({
                    "title": item.title,
                    "href": item.href,
                    "children": [],
                })

    @property
    def title(self) -> str:
        """Book title."""
        return self._metadata.get("title", "Unknown Title")

    @property
    def author(self) -> str:
        """Book author."""
        return self._metadata.get("author", "Unknown Author")

    @property
    def chapters(self) -> list[Chapter]:
        """All chapters in spine order."""
        return self._chapters

    @property
    def toc(self) -> list[dict[str, object]]:
        """Table of contents."""
        return self._toc

    @property
    def metadata(self) -> dict[str, str]:
        """Book metadata."""
        return self._metadata

    def get_chapter(self, index: int) -> Optional[Chapter]:
        """Get a chapter by its index, loading content lazily if needed."""
        if 0 <= index < len(self._chapters):
            chapter = self._chapters[index]
            if not chapter._loaded:
                chapter.ensure_loaded(self._book)
            return chapter
        return None

    def get_cover_image(self) -> Optional[bytes]:
        """Get the cover image data."""
        if self._book is None:
            return None

        for item in self._book.get_items_of_type(ITEM_COVER):
            return item.get_content()

        cover_meta = self._book.get_metadata("DC", "cover")
        if cover_meta:
            cover_id = cover_meta[0][1].get("content", "")
            cover = self._book.get_item_with_id(cover_id)
            if cover:
                return cover.get_content()

        for item in self._book.get_items():
            name = item.get_name().lower()
            item_id = item.get_id().lower()
            if "cover" in name or "cover" in item_id:
                if item.get_type() in (ITEM_IMAGE, ITEM_COVER):
                    return item.get_content()

        for item in self._book.get_items_of_type(ITEM_IMAGE):
            if "cover" in item.get_name().lower():
                return item.get_content()

        return None

    @property
    def total_chapters(self) -> int:
        """Total number of chapters."""
        return len(self._chapters)

    _IMG_SRC_RE = re.compile(r'(<img\s[^>]*?)src=(["\'])([^"\']+)\2', re.IGNORECASE)
    _SVG_HREF_RE = re.compile(
        r'(<image\s[^>]*?)(?:xlink:)?href=(["\'])([^"\']+)\2', re.IGNORECASE
    )

    def resolve_images(self, html: str) -> str:
        """Replace relative image src with base64 data URLs from the EPUB.

        Handles both <img> tags and SVG <image> tags (xlink:href).
        Uses regex for fast replacement without parsing the entire HTML.
        """
        if self._book is None or not self._image_cache:
            return html
        if "<img " not in html and "<image " not in html:
            return html

        html = self._IMG_SRC_RE.sub(self._replace_img_src, html)
        html = self._SVG_HREF_RE.sub(self._replace_svg_href, html)
        return html

    def _replace_img_src(self, m: re.Match) -> str:
        prefix, quote, src = m.group(1), m.group(2), m.group(3)
        if src.startswith("data:"):
            return m.group(0)
        image_item = self._find_image_item(src)
        if image_item is None:
            return m.group(0)
        data = image_item.get_content()
        if not data:
            return m.group(0)
        mime = self._get_mime(image_item.get_name())
        b64 = base64.b64encode(data).decode("ascii")
        return f'{prefix}src={quote}data:{mime};base64,{b64}{quote}'

    def _replace_svg_href(self, m: re.Match) -> str:
        prefix, quote, href = m.group(1), m.group(2), m.group(3)
        if href.startswith("data:"):
            return m.group(0)
        image_item = self._find_image_item(href)
        if image_item is None:
            return m.group(0)
        data = image_item.get_content()
        if not data:
            return m.group(0)
        mime = self._get_mime(image_item.get_name())
        b64 = base64.b64encode(data).decode("ascii")
        return f'{prefix}xlink:href={quote}data:{mime};base64,{b64}{quote} href={quote}data:{mime};base64,{b64}{quote}'

    @staticmethod
    def _get_mime(name: str) -> str:
        name = name.lower()
        if name.endswith(".png"):
            return "image/png"
        if name.endswith(".gif"):
            return "image/gif"
        return "image/jpeg"

    def _find_image_item(self, src: str):
        """Find an image item in the EPUB by its src path.

        Uses the pre-built image cache for fast lookup.
        """
        if self._book is None:
            return None
        normalized = src.replace("\\", "/")
        if normalized.startswith("../"):
            normalized = normalized[3:]

        # Fast path: cache lookup
        item = self._image_cache.get(normalized)
        if item is not None:
            return item
        basename = normalized.rsplit("/", 1)[-1] if "/" in normalized else normalized
        item = self._image_cache.get(basename)
        if item is not None:
            return item

        # Slow path: linear scan (should rarely be needed)
        for item in self._book.get_items():
            if item.get_type() not in (ITEM_IMAGE, ITEM_COVER):
                continue
            item_name = item.get_name().replace("\\", "/")
            if item_name == normalized or item_name.endswith("/" + normalized) or item_name.endswith(normalized):
                self._image_cache[normalized] = item
                return item
        return None

    def resolve_chapter_link(self, href: str) -> Optional[int]:
        """Resolve an internal EPUB href to a chapter index in the spine.

        Args:
            href: Internal link like 'chapter1.xhtml#anchor' or 'chapter1.xhtml'

        Returns:
            Chapter index if found, None otherwise.
        """
        if self._book is None:
            return None
        target_file = href.split("#")[0]
        if not target_file:
            return None
        target_normalized = target_file.replace("\\", "/")
        chapter_idx = 0
        for item_id, _linear in self._book.spine:
            item = self._book.get_item_with_id(item_id)
            if item is None or item.get_type() != ITEM_DOCUMENT:
                continue
            item_name = item.get_name().replace("\\", "/")
            if item_name == target_normalized or item_name.endswith("/" + target_normalized):
                return chapter_idx
            chapter_idx += 1
        return None
