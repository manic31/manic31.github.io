"""홈페이지 정리 스크립트 (매일 새벽 물때 받기 다음에 GitHub Actions가 돌린다)

1) 블로그 최근 글: 네이버 블로그 RSS에서 제목·요약·썸네일·링크만 받아 첫 화면에 넣는다.
   (글 전체를 복사하지 않는다 — 중복 글은 검색·애드센스에 불리)
2) 낚시 노트: notes/ 폴더의 글을 읽어 목록 페이지(notes.html)와 첫 화면 칸을 만든다.
3) 검색엔진용: 페이지마다 원본 주소(canonical), sitemap.xml, robots.txt를 만든다.

도메인을 사면 아래 SITE_URL 한 줄만 바꾸면 된다.
표준 라이브러리만 쓴다.  실행: python tools/build.py
"""
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

SITE_URL = "https://manic31.github.io"   # ← 도메인을 사면 여기만 바꾼다 (끝에 / 없이)
BLOG_RSS = "https://rss.blog.naver.com/manic31.xml"
BLOG_COUNT = 4

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = timezone(timedelta(hours=9))
SKIP_DIRS = {"tools", ".github", ".git", ".claude", "data", "assets"}


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def write(p, text):
    path = os.path.join(ROOT, p)
    old = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    if old != text:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("갱신:", p)


def between(text, name, inner):
    """<!-- name:start --> ... <!-- name:end --> 사이를 바꾼다."""
    pat = re.compile(rf"(<!-- {name}:start -->)(.*?)(<!-- {name}:end -->)", re.S)
    if not pat.search(text):
        raise RuntimeError(f"표시 <!-- {name}:start/end --> 가 없습니다")
    return pat.sub(lambda m: m.group(1) + inner + m.group(3), text)


def esc(s):
    return html.escape(s or "", quote=True)


# ── 1) 블로그 최근 글 ─────────────────────────────────────────
def fetch_blog():
    req = urllib.request.Request(BLOG_RSS, headers={"User-Agent": "darigeonneo-site-build"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    posts = []
    for it in root.find("channel").findall("item")[:BLOG_COUNT]:
        desc = it.findtext("description") or ""
        img = re.search(r'<img[^>]+src="([^"]+)"', desc)
        text = re.sub(r"<[^>]+>", " ", desc)
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        text = re.sub(r"^안녕하세요[,.!]?\s*(다리 건너 낚시입니다[.!]?)?\s*", "", text)  # 매번 같은 인사말은 빼고 요약
        link = (it.findtext("link") or "").split("?")[0]
        try:
            d = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST).strftime("%Y-%m-%d")
        except Exception:
            d = ""
        posts.append({"title": (it.findtext("title") or "").strip(), "link": link, "date": d,
                      "category": (it.findtext("category") or "").strip(),
                      "summary": text[:70] + ("…" if len(text) > 70 else ""),
                      "image": img.group(1) if img else ""})
    return posts


def blog_html(posts):
    if not posts:
        return "\n"
    cards = []
    for p in posts:
        thumb = (f'<img src="{esc(p["image"])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
                 if p["image"] else '<span class="noimg"></span>')
        md = p["date"][5:].replace("-", "/") if p["date"] else ""
        cards.append(f'''
      <a class="bpost" href="{esc(p["link"])}" target="_blank" rel="noopener">
        <div class="th">{thumb}</div>
        <div class="tx"><div class="bt">{esc(p["title"])}</div><div class="bs">{esc(p["summary"])}</div>
        <div class="bm">{esc(p["category"])}{" · " if p["category"] and md else ""}{md}</div></div>
      </a>''')
    return f'''
  <section>
    <div class="sec-head"><h2>블로그 최근 글</h2><a class="more" href="https://blog.naver.com/manic31" target="_blank" rel="noopener">블로그로 →</a></div>
    <div class="blist">{"".join(cards)}
    </div>
  </section>
  '''


# ── 2) 낚시 노트 ──────────────────────────────────────────────
def meta(text, name):
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', text)
    return html.unescape(m.group(1)) if m else ""


def load_notes():
    notes = []
    d = os.path.join(ROOT, "notes")
    if not os.path.isdir(d):
        return notes
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html") or fn.startswith("_"):
            continue
        t = read(f"notes/{fn}")
        title = re.search(r"<title>(.*?)</title>", t, re.S)
        title = html.unescape(title.group(1)).split(" · 다리 건너 낚시")[0].strip() if title else fn
        notes.append({"file": f"notes/{fn}", "title": title, "desc": meta(t, "description"),
                      "date": meta(t, "date"), "tag": meta(t, "note-tag")})
    notes.sort(key=lambda n: n["date"], reverse=True)
    return notes


def note_items(notes, base=""):
    return "".join(f'''
      <a class="note-item" href="{base}{esc(n["file"])}">
        <div class="nm">{esc(n["tag"])}{" · " if n["tag"] else ""}{esc(n["date"].replace("-", "."))}</div>
        <div class="nt">{esc(n["title"])}</div><div class="nd">{esc(n["desc"])}</div>
      </a>''' for n in notes)


def home_notes_html(notes):
    if not notes:
        return "\n"
    return f'''
  <section>
    <div class="sec-head"><h2>낚시 노트</h2><a class="more" href="notes.html">전체 보기 →</a></div>
    <div class="nlist">{note_items(notes[:3])}
    </div>
  </section>
  '''


# ── 3) 원본 주소·사이트 지도 ─────────────────────────────────
def public_pages():
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT).replace("\\", "/")
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith(".")]
        for fn in filenames:
            if fn.endswith(".html") and not fn.startswith("_"):
                pages.append(fn if rel == "." else f"{rel}/{fn}")
    return sorted(pages)


def page_url(p):
    return f"{SITE_URL}/" if p == "index.html" else f"{SITE_URL}/{p}"


def set_canonical(p):
    t = read(p)
    tag = f'<link rel="canonical" href="{page_url(p)}">'
    if 'rel="canonical"' in t:
        t2 = re.sub(r'<link rel="canonical" href="[^"]*">', tag, t)
    else:
        t2 = re.sub(r"(</title>\n)", r"\1" + tag + "\n", t, count=1)
    write(p, t2)


def main():
    # 블로그 글 (실패하면 지난번 것을 그대로 둔다)
    index = read("index.html")
    try:
        posts = fetch_blog()
        with open(os.path.join(ROOT, "data", "blog.json"), "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=1)
        index = between(index, "blog", blog_html(posts))
    except Exception as e:
        print("블로그 글을 못 받아서 이전 것을 유지합니다:", e, file=sys.stderr)

    notes = load_notes()
    index = between(index, "notes", home_notes_html(notes))
    write("index.html", index)

    nt = read("notes.html")
    empty = '\n      <p class="empty">아직 정리한 글이 없어요.</p>' if not notes else note_items(notes)
    nt = between(nt, "list", empty + "\n    ")
    # 글이 없을 땐 빈 페이지를 검색에 내지 않고(noindex), 첫 글이 생기면 자동으로 뺀다
    noindex = '<meta name="robots" content="noindex">'
    if not notes and noindex not in nt:
        nt = re.sub(r"(</title>\n)", r"\1" + noindex + "\n", nt, count=1)
    elif notes:
        nt = nt.replace(noindex + "\n", "")
    write("notes.html", nt)

    pages = public_pages()
    if not notes:  # 글이 없을 땐 빈 목록 페이지를 검색에 내지 않는다
        pages = [p for p in pages if p != "notes.html"]
    for p in public_pages():
        set_canonical(p)

    dates = {n["file"]: n["date"] for n in notes}
    urls = "".join(f"  <url><loc>{page_url(p)}</loc>{f'<lastmod>{dates[p]}</lastmod>' if dates.get(p) else ''}</url>\n"
                   for p in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /tools/\n\nSitemap: {SITE_URL}/sitemap.xml\n")


if __name__ == "__main__":
    main()
