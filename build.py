#!/usr/bin/env python3
"""Builds the site into dist/. Usage: python3 build.py"""
import html
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SRC = ROOT / "photographers"
DIST = ROOT / "dist"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}
FONT = "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..600;1,9..144,300..600&display=swap"


def parse_md(path):
    """Frontmatter (key: value between ---) + body. ponytail: no yaml/md lib."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body.strip()


def paragraphs(text):
    return "\n".join(
        f"<p>{html.escape(p.strip())}</p>" for p in text.split("\n\n") if p.strip()
    )


def display_title(title):
    """Last word in italics: 'Olhares <em>Capixabas</em>'."""
    head, _, last = html.escape(title).rpartition(" ")
    return f"{head} <em>{last}</em>" if head else last


EXTERNAL = ' target="_blank" rel="noopener"'


def links_html(meta, skip=("name", "bio", "title")):
    """Any non-reserved frontmatter key becomes a link; bare emails get mailto:."""
    return "\n".join(
        f'<a href="mailto:{html.escape(url)}">{html.escape(label)}</a>'
        if "@" in url and ":" not in url else
        f'<a href="{html.escape(url)}"{EXTERNAL}>{html.escape(label)}</a>'
        for label, url in meta.items()
        if label not in skip
    )


def excerpt(text, limit=160):
    """First paragraph as a single plain-text line, truncated for meta description."""
    first = " ".join(text.split("\n\n")[0].split())
    return first if len(first) <= limit else first[:limit].rsplit(" ", 1)[0] + "…"


def page(title, body, depth=0, desc="", site_name="", canonical="", image=""):
    css = "../" * depth + "style.css"
    e = html.escape
    seo = f'<meta name="description" content="{e(desc)}">\n' if desc else ""
    seo += f'<meta property="og:title" content="{e(title)}">\n'
    if desc:
        seo += f'<meta property="og:description" content="{e(desc)}">\n'
    seo += '<meta property="og:type" content="website">\n'
    seo += '<meta property="og:locale" content="pt_BR">\n'
    if site_name:
        seo += f'<meta property="og:site_name" content="{e(site_name)}">\n'
    if canonical:
        seo += f'<link rel="canonical" href="{e(canonical)}">\n'
        seo += f'<meta property="og:url" content="{e(canonical)}">\n'
    if image:
        seo += f'<meta property="og:image" content="{e(image)}">\n'
    seo += f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">'
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
{seo}
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONT}">
<link rel="stylesheet" href="{css}">
</head>
<body>
{body}
</body>
</html>
"""


def build():
    site, intro = parse_md(ROOT / "index.md")
    title = site["title"]
    period = site.get("period", "")
    # absolute URLs (canonical, og:image) only work with a real domain in `url:`
    base = site.get("url", "").rstrip("/")

    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    shutil.copy(ROOT / "style.css", DIST / "style.css")

    # standalone pages: any root .md besides index.md becomes /<name>/
    pages = []
    for md in sorted(ROOT.glob("*.md")):
        if md.name in ("index.md", "README.md"):
            continue
        meta, text = parse_md(md)
        page_title = meta.get("title", md.stem)
        out = DIST / md.stem
        out.mkdir()
        bio = f'\n<p class="bio">{html.escape(meta["bio"])}</p>' if "bio" in meta else ""
        links = links_html(meta)
        links = f'\n<p class="links">{links}</p>' if links else ""
        body = f"""<nav class="bar">
<a href="../">← {html.escape(title)}</a>
<span>{html.escape(period)}</span>
</nav>
<header class="artist">
<h1>{display_title(meta.get("name", page_title))}</h1>{bio}{links}
</header>
<main>
<div class="statement">
{paragraphs(text)}
</div>
</main>
"""
        (out / "index.html").write_text(
            page(f"{page_title} — {title}", body, depth=1, desc=excerpt(text),
                 site_name=title, canonical=base and f"{base}/{md.stem}/"),
            encoding="utf-8")
        pages.append((page_title, md.stem))

    photographers = []
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir()):
        meta, statement = parse_md(folder / "info.md")
        slug = folder.name
        out = DIST / slug
        out.mkdir()

        photos = sorted(f for f in folder.iterdir() if f.suffix.lower() in IMG_EXTS)
        for f in photos:
            shutil.copy(f, out / f.name)

        name = html.escape(meta["name"])
        links = links_html(meta)
        gallery = "\n".join(
            f'<figure><img src="{html.escape(f.name)}" alt="Fotografia de {name}" loading="lazy">'
            f"<figcaption>{n:02d}</figcaption></figure>"
            for n, f in enumerate(photos, 1)
        )
        body = f"""<nav class="bar">
<a href="../">← {html.escape(title)}</a>
<span>{html.escape(period)}</span>
</nav>
<header class="artist">
<h1>{display_title(meta["name"])}</h1>
<p class="bio">{html.escape(meta.get("bio", ""))}</p>
<p class="links">{links}</p>
</header>
<main>
<div class="statement">
{paragraphs(statement)}
</div>
<section class="gallery">
{gallery}
</section>
</main>
"""
        (out / "index.html").write_text(
            page(f'{meta["name"]} — {title}', body, depth=1,
                 desc=excerpt(statement) or meta.get("bio", ""), site_name=title,
                 canonical=base and f"{base}/{slug}/",
                 image=base and photos and f"{base}/{slug}/{photos[0].name}" or ""),
            encoding="utf-8")
        photographers.append((meta["name"], slug))

    photographers.sort(key=lambda p: p[0].lower())
    items = "\n".join(
        f'<li><a href="{html.escape(slug)}/"><span class="num">{n:02d}</span>'
        f"<span class=\"name\">{html.escape(name)}</span></a></li>"
        for n, (name, slug) in enumerate(photographers, 1)
    )
    body = f"""<header class="home">
<p class="kicker"><span>Exposição fotográfica</span><span>{html.escape(title)}</span></p>
<div class="masthead">
<h1>{display_title(title)}</h1>
<p class="curator"><span class="label">Curadoria</span>{f'<a href="curadoria/">{html.escape(site.get("curator", ""))}</a>' if (ROOT / "curadoria.md").exists() else html.escape(site.get("curator", ""))}</p>
</div>
<p class="tagline">{html.escape(site.get("tagline", ""))}</p>
<div class="details">
<div>
<p class="label">Quando</p>
<p class="detail-value">{html.escape(period)}</p>
</div>
<div>
<p class="label">Onde</p>
<p class="detail-value">{html.escape(site.get("venue", ""))}</p>
<p class="detail-address"><a href="https://maps.google.com/?q={quote(site.get("venue", "") + ", " + site.get("address", ""))}"{EXTERNAL}>{html.escape(site.get("address", ""))}</a></p>
</div>
</div>
</header>
<main>
<div class="intro">
{paragraphs(intro)}
</div>
<p class="label">{len(photographers)} fotógrafos</p>
<ol class="photographers">
{items}
</ol>
</main>
<footer class="foot">
<span>{" · ".join(f'<a href="{html.escape(slug)}/">{html.escape(t)}</a>' for t, slug in pages)}</span>
<span>webdesign by <a href="https://www.linkedin.com/in/felipelube"{EXTERNAL}>Felipe Lube</a></span>
</footer>
"""
    (DIST / "index.html").write_text(
        page(title, body, desc=site.get("tagline", "") or excerpt(intro),
             site_name=title, canonical=base and f"{base}/"),
        encoding="utf-8")

    if base:
        urls = [f"{base}/"] + [f"{base}/{slug}/" for _, slug in pages + photographers]
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
            + "\n</urlset>\n", encoding="utf-8")
        (DIST / "robots.txt").write_text(f"Sitemap: {base}/sitemap.xml\n", encoding="utf-8")

    assert (DIST / "index.html").exists() and photographers, "empty build"
    print(f"ok: {len(photographers)} photographer(s) in {DIST}")


if __name__ == "__main__":
    build()
