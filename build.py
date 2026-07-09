#!/usr/bin/env python3
"""Builds the site into dist/. Usage: python3 build.py"""
import html
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote

MONTHS = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()

ROOT = Path(__file__).parent
SRC = ROOT / "photographers"
DIST = ROOT / "dist"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}
FONT = "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,WONK@0,9..144,300..600,0..1;1,9..144,300..600,0..1&display=swap"


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

# the site's only JavaScript: arrow keys / Escape for the lightbox
LIGHTBOX_KEYS = """<script>
addEventListener("keydown", e => {
  const open = document.querySelector(".lightbox:target");
  if (!open) return;
  const boxes = [...document.querySelectorAll(".lightbox")], i = boxes.indexOf(open);
  if (e.key === "Escape") location.replace(open.querySelector(".shut").hash);
  else if (e.key === "ArrowRight") location.replace("#" + boxes[(i + 1) % boxes.length].id);
  else if (e.key === "ArrowLeft") location.replace("#" + boxes[(i - 1 + boxes.length) % boxes.length].id);
});
</script>
"""


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


def page(title, body, depth=0, desc="", site_name="", canonical="", image="", accent=""):
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
<body{f' style="--accent: {accent}"' if accent else ""}>
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
    # photos are held back until the exposition opens; rebuild on opening day to publish them
    opening = date.fromisoformat(site["start"]) if "start" in site else None
    started = opening is None or date.today() >= opening
    opening_label = "" if started else f"{opening.day:02d} de {MONTHS[opening.month - 1]}"

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

    folders = sorted(p for p in SRC.iterdir() if p.is_dir())
    # one accent hue per photographer — even hue steps, same sat/light so they sit quietly on black
    palette = [f"hsl({15 + i * 360 // len(folders)} 40% 62%)" for i in range(len(folders))]
    photographers = []
    for i, folder in enumerate(folders):
        meta, statement = parse_md(folder / "info.md")
        slug = folder.name
        accent = palette[i]
        out = DIST / slug
        out.mkdir()

        photos = sorted(f for f in folder.iterdir() if f.suffix.lower() in IMG_EXTS)
        name = html.escape(meta["name"])
        links = links_html(meta)
        if started:
            for f in photos:
                shutil.copy(f, out / f.name)
            # click a photo → CSS :target lightbox; closing links back to the thumbnail
            gallery = "\n".join(
                f'<figure id="g-{n:02d}"><a href="#foto-{n:02d}">'
                f'<img src="{html.escape(f.name)}" alt="Fotografia de {name}" loading="lazy"></a>'
                f"<figcaption>{n:02d}</figcaption></figure>"
                for n, f in enumerate(photos, 1)
            )
            def thumbs(current):
                parts = []
                for m, g in enumerate(photos, 1):
                    cls = ' class="current"' if m == current else ""
                    parts.append(f'<a href="#foto-{m:02d}"{cls}>'
                                 f'<img src="{html.escape(g.name)}" alt="" loading="lazy"></a>')
                return "".join(parts)

            # overlays live outside .gallery so its nth-child rhythm rules can't touch them
            overlays = "\n".join(
                f'<figure class="lightbox" id="foto-{n:02d}">'
                f'<a class="shut" href="#g-{n:02d}"><img src="{html.escape(f.name)}" alt="Fotografia de {name}"></a>'
                f"<nav>{thumbs(n)}</nav></figure>"
                for n, f in enumerate(photos, 1)
            )
        else:
            overlays = ""
            gallery = f'<p class="label">Fotografias a partir de {opening_label}</p>\n' + "\n".join(
                f'<figure><div class="placeholder"><span>{n:02d}</span></div></figure>'
                for n in range(1, len(photos) + 1)
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
{overlays}
</main>
{LIGHTBOX_KEYS if started and photos else ""}"""
        (out / "index.html").write_text(
            page(f'{meta["name"]} — {title}', body, depth=1,
                 desc=excerpt(statement) or meta.get("bio", ""), site_name=title,
                 canonical=base and f"{base}/{slug}/",
                 image=base and started and photos and f"{base}/{slug}/{photos[0].name}" or "",
                 accent=accent),
            encoding="utf-8")
        photographers.append((meta["name"], slug, accent))

    photographers.sort(key=lambda p: p[0].lower())
    items = "\n".join(
        f'<li style="--accent: {accent}"><a href="{html.escape(slug)}/"><span class="num">{n:02d}</span>'
        f"<span class=\"name\">{html.escape(name)}</span></a></li>"
        for n, (name, slug, accent) in enumerate(photographers, 1)
    )
    body = f"""<header class="home">
<p class="kicker"><span>Exposição fotográfica</span><span>{html.escape(title)}</span></p>
{f'<p class="opening"><span class="dot"></span>Abertura em {opening_label}</p>' if opening_label else ""}
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
        urls = [f"{base}/"] + [f"{base}/{p[1]}/" for p in pages + photographers]
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
            + "\n</urlset>\n", encoding="utf-8")
        (DIST / "robots.txt").write_text(f"Sitemap: {base}/sitemap.xml\n", encoding="utf-8")

    assert (DIST / "index.html").exists() and photographers, "empty build"
    state = "photos published" if started else f"placeholders until {opening}"
    print(f"ok: {len(photographers)} photographer(s) in {DIST} — {state}")


if __name__ == "__main__":
    build()
