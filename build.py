#!/usr/bin/env python3
"""Gera o site em dist/. Uso: python3 build.py"""
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
    """Frontmatter (chave: valor entre ---) + corpo. ponytail: sem lib de yaml/md."""
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
    """Última palavra em itálico: 'Olhares <em>Capixabas</em>'."""
    head, _, last = html.escape(title).rpartition(" ")
    return f"{head} <em>{last}</em>" if head else last


def page(title, body, depth=0):
    css = "../" * depth + "style.css"
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
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

    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    shutil.copy(ROOT / "style.css", DIST / "style.css")

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
        # qualquer chave além de name/bio vira link: "instagram: https://..."
        links = "\n".join(
            f'<a href="{html.escape("mailto:" + url if "@" in url and ":" not in url else url)}">{html.escape(label)}</a>'
            for label, url in meta.items()
            if label not in ("name", "bio")
        )
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
        (out / "index.html").write_text(page(f'{meta["name"]} — {title}', body, depth=1), encoding="utf-8")
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
<p class="curator"><span class="label">Curadoria</span>{html.escape(site.get("curator", ""))}</p>
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
<p class="detail-address"><a href="https://maps.google.com/?q={quote(site.get("venue", "") + ", " + site.get("address", ""))}">{html.escape(site.get("address", ""))}</a></p>
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
"""
    (DIST / "index.html").write_text(page(title, body), encoding="utf-8")

    assert (DIST / "index.html").exists() and photographers, "build vazio"
    print(f"ok: {len(photographers)} fotógrafo(s) em {DIST}")


if __name__ == "__main__":
    build()
