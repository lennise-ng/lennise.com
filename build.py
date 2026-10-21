#!/usr/bin/env python3
"""
Builds lennise.com from the files in content/ into docs/.

    python3 build.py

That is the whole thing. No framework, no configuration file.
The only dependency is the `markdown` package:  pip install markdown

How it works, top to bottom:
  1. read every essay in content/essays/   (one Markdown file each)
  2. read content/margins.md               (short notes, one file)
  3. read content/letters/<essay-slug>.md  (reader replies, one file per essay)
  4. read content/about.md
  5. fill the HTML templates in templates/ and write them into docs/
  6. copy static/ (CSS and images) into docs/
  7. write docs/feed.xml (RSS)
"""

import html
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "docs"

SITE_URL = "https://www.lennise.com"
SITE_NAME = "Lennise"
SITE_TAGLINE = "Reflections on art, business and history · written from 🇲🇾 🇸🇬 🇯🇵"
EMAIL = "hello@lennise.com"  # change this to the address you want letters sent to

MD = markdown.Markdown(extensions=["smarty", "footnotes", "tables"])


# ---------------------------------------------------------------- helpers

def md(text):
    """Markdown → HTML. Reset between calls so footnote numbering restarts."""
    MD.reset()
    return MD.convert(text.strip())


def read_front_matter(path):
    """
    Split a file into (metadata, body).
    Metadata is the block of `key: value` lines between two `---` lines at the top.
    """
    text = path.read_text(encoding="utf-8")
    meta = {}
    if text.startswith("---"):
        _, block, body = text.split("---", 2)
        for line in block.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
    else:
        body = text
    return meta, body


def render(template_name, **vars):
    """Fill {{name}} holes in a template. No logic in templates on purpose."""
    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, value in vars.items():
        tpl = tpl.replace("{{" + key + "}}", str(value))
    return tpl


def page(title, body, description=""):
    """Wrap page content in the base layout."""
    return render(
        "base.html",
        title=html.escape(title),
        description=html.escape(description),
        site_name=SITE_NAME,
        tagline=SITE_TAGLINE,
        email=EMAIL,
        body=body,
        year=datetime.now().year,
    )


def nice_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {d.strftime('%B %Y')}"


def short_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {d.strftime('%b')}"


def reading_time(text):
    words = len(re.findall(r"\w+", text))
    return max(1, round(words / 220))


def write(rel_path, content):
    path = OUT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def split_entries(text):
    """
    margins.md and letters files are lists of entries, each starting with a
    '## heading' line. Returns [(heading, body_markdown), ...] in file order.
    """
    entries = []
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                entries.append(current)
            current = [line[3:].strip(), []]
        elif current:
            current[1].append(line)
    if current:
        entries.append(current)
    return [(h, "\n".join(b)) for h, b in entries]


# ----------------------------------------------------------------- content

def load_essays():
    essays = []
    for path in sorted((CONTENT / "essays").glob("*.md")):
        meta, body = read_front_matter(path)
        if meta.get("draft", "").lower() == "true":
            continue
        slug = path.stem
        # allow a leading date in the filename: 2026-10-14-some-title.md → some-title
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
        essays.append({
            "slug": slug,
            "title": meta.get("title", slug.replace("-", " ").title()),
            "date": meta["date"],
            "subtitle": meta.get("subtitle", ""),
            "tags": meta.get("tags", ""),
            "series": meta.get("series", ""),
            "image": meta.get("image", ""),
            "image_caption": meta.get("image_caption", ""),
            "body_md": body,
            "body": md(body),
            "minutes": reading_time(body),
            "url": f"/essays/{slug}/",
        })
    essays.sort(key=lambda e: e["date"], reverse=True)
    return essays


def load_letters(slug):
    path = CONTENT / "letters" / f"{slug}.md"
    if not path.exists():
        return []
    # escape the heading here, once; it is treated as safe HTML from now on
    return [(html.escape(who), body) for who, body in split_entries(path.read_text(encoding="utf-8"))]


def load_margins():
    path = CONTENT / "margins.md"
    if not path.exists():
        return []
    entries = split_entries(path.read_text(encoding="utf-8"))
    entries.sort(key=lambda e: e[0], reverse=True)  # heading is the ISO date
    return entries


# ------------------------------------------------------------------ pieces

def essay_list_item(e):
    return render(
        "_essay_item.html",
        url=e["url"],
        title=html.escape(e["title"]),
        subtitle=html.escape(e["subtitle"]),
        date=nice_date(e["date"]),
        iso=e["date"],
    )


def letters_block(letters, heading="Letters on this essay"):
    if not letters:
        return ""
    items = "".join(
        render("_letter.html", body=md(body), who=who)
        for who, body in letters
    )
    return render("_letters.html", heading=heading, items=items)


def split_margin(body):
    """
    A margin entry is plain Markdown, optionally with a title on its first
    line ('### Title') and tags on its last line ('tags: A · B'). Both are
    optional, so the older one-line entries need no change.
    Returns (title, tags, body_markdown).
    """
    lines = body.strip().splitlines()
    title = tags = ""
    if lines and lines[0].startswith("### "):
        title = lines.pop(0)[4:].strip()
    if lines and lines[-1].lower().startswith("tags:"):
        tags = lines.pop()[5:].strip()
    return title, tags, "\n".join(lines)


def margins_block(entries, limit=None):
    if limit:
        entries = entries[:limit]
    out = []
    for iso, raw in entries:
        title, tags, body = split_margin(raw)
        out.append(render(
            "_margin.html",
            iso=iso,
            date=short_date(iso),
            title=f'<p class="margin-title">{html.escape(title)}</p>' if title else "",
            body=md(body),
            tags=f'<p class="meta">{html.escape(tags)}</p>' if tags else "",
        ))
    return "".join(out)


# ------------------------------------------------------------------- build

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    essays = load_essays()
    margins = load_margins()
    about_meta, about_md = read_front_matter(CONTENT / "about.md")

    # --- individual essay pages
    for i, e in enumerate(essays):
        newer = essays[i - 1] if i > 0 else None
        older = essays[i + 1] if i + 1 < len(essays) else None
        figure = ""
        if e["image"]:
            figure = render(
                "_figure.html",
                src=e["image"],
                alt=html.escape(e["image_caption"] or e["title"]),
                caption=html.escape(e["image_caption"]),
            )
        body = render(
            "essay.html",
            title=html.escape(e["title"]),
            subtitle=html.escape(e["subtitle"]),
            tags=html.escape(" · ".join(x for x in (e["series"], e["tags"]) if x)),
            date=nice_date(e["date"]),
            iso=e["date"],
            minutes=e["minutes"],
            figure=figure,
            body=e["body"],
            letters=letters_block(load_letters(e["slug"])),
            newer=f'<a href="{newer["url"]}">← {html.escape(newer["title"])}</a>' if newer else "",
            older=f'<a href="{older["url"]}">{html.escape(older["title"])} →</a>' if older else "",
            email=EMAIL,
        )
        write(f"essays/{e['slug']}/index.html", page(e["title"], body, e["subtitle"]))

    # --- home
    latest = essays[0] if essays else None
    featured = ""
    if latest:
        featured = render(
            "_featured.html",
            url=latest["url"],
            title=html.escape(latest["title"]),
            subtitle=html.escape(latest["subtitle"]),
            date=nice_date(latest["date"]),
            minutes=latest["minutes"],
            image=(f'<img src="{latest["image"]}" alt="{html.escape(latest["image_caption"] or latest["title"])}">'
                   if latest["image"] else ""),
        )
    # all letters, newest essay first, for the homepage
    home_letters = []
    for e in essays:
        for who, body in load_letters(e["slug"]):
            home_letters.append((f'{who}, on <a href="{e["url"]}">{html.escape(e["title"])}</a>', body))
    body = render(
        "index.html",
        featured=featured,
        earlier=("" if len(essays) < 2 else
                 '<section class="essay-list">\n  <h2 class="label">Earlier essays</h2>\n'
                 + "".join(essay_list_item(e) for e in essays[1:])
                 + '\n  <p class="more"><a href="/essays/">All essays →</a></p>\n</section>'),
        margins=margins_block(margins, limit=3),
        letters=(letters_block(home_letters[:2], heading="Letters") if home_letters
                 else '<h2 class="label">Letters</h2>'),
        email=EMAIL,
    )
    write("index.html", page(SITE_NAME, body, SITE_TAGLINE))

    # --- essays archive
    body = render("archive.html", essays="".join(essay_list_item(e) for e in essays))
    write("essays/index.html", page("Essays", body))

    # --- margins
    body = render("margins.html", margins=margins_block(margins))
    write("margins/index.html", page("Margins", body))

    # --- about
    body = render("about.html", body=md(about_md), email=EMAIL)
    write("about/index.html", page("About", body))

    # --- RSS
    items = "".join(
        render(
            "_rss_item.html",
            title=html.escape(e["title"]),
            url=SITE_URL + e["url"],
            date=datetime.strptime(e["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                     .strftime("%a, %d %b %Y 08:00:00 +0000"),
            description=html.escape(e["subtitle"]),
            content=html.escape(e["body"]),
        )
        for e in essays[:20]
    )
    write("feed.xml", render("feed.xml", site_url=SITE_URL, site_name=SITE_NAME,
                             tagline=SITE_TAGLINE, items=items))

    # --- static files, CNAME, no-Jekyll marker
    shutil.copytree(STATIC, OUT / "static")
    write("CNAME", "www.lennise.com\n")
    write(".nojekyll", "")

    print(f"built {len(essays)} essays, {len(margins)} margin notes → docs/")


if __name__ == "__main__":
    build()
