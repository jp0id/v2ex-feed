import re
from html import escape
from html.parser import HTMLParser
from itertools import count
from typing import Optional

from bs4 import BeautifulSoup, NavigableString

# 常量

MAX_TG_CHARS = 4000
ELLIPSIS = "…"

HEADINGS = {f"h{i}" for i in range(1, 7)}

ALLOWED_TAG_ATTRS = {
    "b": [], "strong": [], "i": [], "em": [],
    "u": [], "ins": [], "s": [], "strike": [], "del": [],
    "span": ["class"], "tg-spoiler": [],
    "a": ["href"], "tg-emoji": ["emoji-id"],
    "code": ["class"], "pre": [],
    "blockquote": ["expandable"],
}

LANG_TOKEN = re.compile(r"language-[\w+-]+$")


# 工具函数

def _attrs_to_str(attrs):
    return "".join(
        f' {k}' if v is None else f' {k}="{escape(v, quote=True)}"' for k, v in attrs
    )


# HTML 清洗

# CHANGED: Optional[str] + 空内容直接返回 ""
def _sanitize_html(html_text: Optional[str]) -> str:
    """
    收敛 HTML 为 Telegram 支持的子集；允许 None/空串直接返回 "".
    """
    if not html_text:
        return ""

    if not isinstance(html_text, str):
        html_text = str(html_text)

    soup = BeautifulSoup(html_text, "lxml")

    for node in soup(["script", "style"]):
        node.decompose()

    img_no, vid_no = count(1), count(1)

    for tag in list(soup.find_all(True)):
        name = tag.name

        if name in HEADINGS:
            tag.name = "b"
            continue

        if name in ("ul", "ol"):
            items = tag.find_all("li", recursive=False)
            if name == "ul":
                lines = [f"• {escape(li.get_text(strip=True))}" for li in items]
            else:
                lines = [
                    f"{idx}. {escape(li.get_text(strip=True))}"
                    for idx, li in enumerate(items, 1)
                ]
            tag.replace_with(NavigableString("\n".join(lines)))
            continue

        if name == "img":
            src = tag.get("src")
            if src:
                a = soup.new_tag("a", href=src)
                a.string = f"[图片 {next(img_no)}]"
                tag.replace_with(a)
            else:
                tag.decompose()
            continue

        if name == "div" and "embedded_video_wrapper" in tag.get("class", []):
            iframe = tag.find("iframe", src=True)
            if iframe:
                a = soup.new_tag("a", href=iframe["src"])
                a.string = f"[观看视频 {next(vid_no)}]"
                tag.replace_with(a)
            else:
                tag.decompose()
            continue

        if name == "br":
            tag.replace_with(NavigableString("\n"))
            continue

        if name in {"p", "div"}:
            if not tag.contents:
                tag.decompose()
                continue
            if tag.parent and tag.parent.name == "blockquote":
                tag.insert_before(NavigableString("\n"))
            tag.unwrap()
            continue

        if name == "table":
            rows = []
            for tr in tag.find_all("tr", recursive=False):
                cells = []
                for cell in tr.find_all(["td", "th"], recursive=False):
                    txt = escape(cell.get_text(strip=True))
                    if cell.name == "th":
                        txt = f"<b>{txt}</b>"
                    cells.append(txt)
                if cells:
                    rows.append(" | ".join(cells))
            tag.replace_with(NavigableString("\n".join(rows)))
            continue

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAG_ATTRS:
            tag.unwrap()
            continue

        tag.attrs = {k: v for k, v in tag.attrs.items() if k in ALLOWED_TAG_ATTRS[tag.name]}

        if tag.name == "span" and tag.get("class") != ["tg-spoiler"]:
            tag.unwrap()

        if tag.name == "code" and "class" in tag.attrs:
            cls = tag.get("class")
            cls = [cls] if isinstance(cls, str) else cls
            valid = [c for c in cls if LANG_TOKEN.fullmatch(c)]
            tag["class"] = valid if valid else tag.attrs.pop("class", None)

    return str(soup).strip()


# 长度截断器

class _TelegramHTMLTruncator(HTMLParser):
    def __init__(self, limit):
        super().__init__(convert_charrefs=False)
        self.limit = limit
        self.buf, self.len = [], 0
        self.stack = []
        self.done = False

    def _add_raw(self, s: str):
        if self.done:
            return
        need = len(s)
        if self.len + need > self.limit - 1:
            remain = self.limit - 1 - self.len
            if remain > 0:
                self.buf.append(s[:remain])
                self.len += remain
            self.buf.append(ELLIPSIS)
            self.len += 1
            for tag, _ in reversed(self.stack):
                self.buf.append(f"</{tag}>")
            self.done = True
            return
        self.buf.append(s)
        self.len += need

    def handle_starttag(self, tag, attrs):
        attrs_str = _attrs_to_str(attrs)
        self._add_raw(f"<{tag}{attrs_str}>")
        if not self.done:
            self.stack.append((tag, attrs_str))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack.pop(i)
                break
        self._add_raw(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self._add_raw(f"<{tag}{_attrs_to_str(attrs)}/>")

    def handle_data(self, data):
        self._add_raw(data)

    def handle_entityref(self, name):
        self._add_raw(f"&{name};")

    def handle_charref(self, name):
        self._add_raw(f"&#{name};")


def _truncate_html(html_text: str, limit: int = MAX_TG_CHARS) -> str:
    if len(html_text) <= limit:
        return html_text
    parser = _TelegramHTMLTruncator(limit)
    parser.feed(html_text)
    return "".join(parser.buf)


# 公共入口

# CHANGED: Optional[str] + 若 clean == "" 则直接返回 ""
def html_to_telegram(raw_html: Optional[str], limit: int = MAX_TG_CHARS) -> str:
    """
    原始 HTML → Telegram 可发送字符串（超长时尾部自动“…”）。
    空正文返回空串，不抛异常。
    """
    clean = _sanitize_html(raw_html)
    if not clean:
        return ""  # 空内容直接退出
    return _truncate_html(clean, limit)
