#!/usr/bin/env python3
"""Renders an Instagram carousel (1080x1080 PNGs) for a photographer,
reusing the site's design language. Usage: python3 instagram.py <slug>"""
import html
import re
import subprocess
import sys
from pathlib import Path

from build import FONT, IMG_EXTS, MONTHS, ROOT, SRC, parse_md

CHROME = "/usr/bin/google-chrome"
GRAIN = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2' "
         "stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
         "<rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")

CSS = """
:root {{ --bg: {bg}; --ink: #ece9e2; --muted: #8a8a85; --hairline: {hairline};
        --accent: {accent}; --serif: "Fraunces", Georgia, serif; --sans: system-ui, sans-serif; }}
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: 1080px; height: 1080px; overflow: hidden; background: var(--bg); color: var(--ink);
       font-family: var(--sans); line-height: 1.7; position: relative; }}
body::after {{ content: ""; position: fixed; inset: 0; pointer-events: none; opacity: 0.12;
              background: url("{grain}"); }}
.frame {{ position: absolute; inset: 0; padding: 80px; display: flex; flex-direction: column; }}
.kicker, .label, .caption, .bar {{ font-size: 20px; letter-spacing: 0.22em; text-transform: uppercase;
                                   color: var(--muted); line-height: 1.5; }}
.kicker, .bar {{ display: flex; justify-content: space-between; gap: 16px; }}
.kicker {{ padding-bottom: 24px; border-bottom: 1px solid var(--hairline); }}
.bar {{ margin-top: auto; padding-top: 24px; border-top: 1px solid var(--hairline); }}
h1 {{ font-family: var(--serif); font-weight: 340; line-height: 0.95; letter-spacing: -0.01em;
     font-variation-settings: "WONK" 1; font-size: 128px; }}
h1 em {{ font-style: italic; font-weight: 300; color: var(--accent); }}
.grow {{ flex: 1; display: flex; flex-direction: column; justify-content: center; }}
.bio {{ margin-top: 48px; max-width: 720px; color: var(--muted); font-size: 30px; }}
.quote {{ font-family: var(--serif); font-style: italic; font-size: 52px; line-height: 1.4;
         color: #c9c6bf; max-width: 860px; }}
.quote em {{ color: var(--accent); font-style: italic; }}
.prose {{ font-family: var(--serif); font-weight: 340; font-size: 40px; line-height: 1.5;
         color: #c9c6bf; max-width: 880px; }}
.milestones {{ margin-top: 16px; }}
.milestones div {{ display: flex; gap: 48px; padding: 40px 0; border-top: 1px solid var(--hairline);
                  align-items: baseline; }}
.milestones div:first-child {{ border-top: 0; }}
.year {{ font-family: var(--serif); font-style: italic; font-size: 44px; color: var(--accent);
        flex: 0 0 130px; font-variation-settings: "WONK" 1; }}
.milestones p {{ font-size: 27px; color: var(--muted); line-height: 1.55; }}
.milestones .rname {{ font-family: var(--serif); font-weight: 340; font-size: 54px; color: var(--ink);
                     line-height: 1.15; font-variation-settings: "WONK" 1; }}
.roster div {{ padding: 20px 0; }}
.roster .rname {{ font-size: 44px; }}
.photo {{ position: absolute; inset: 0; padding: 80px 80px 150px; display: grid; place-items: center; }}
/* fixed px caps: percentage max-height resolves against the auto grid track, letting tall photos overflow */
.photo img {{ max-width: 920px; max-height: 850px; object-fit: contain; display: block; }}
.caption {{ position: absolute; left: 80px; bottom: 80px; color: var(--ink); }}
.caption em {{ font-family: var(--serif); font-style: italic; color: var(--accent); margin-right: 24px; }}
.details {{ display: flex; gap: 96px; margin-top: 72px; }}
.details .label {{ margin-bottom: 8px; }}
.details p {{ font-size: 28px; }}
.tagline {{ margin-top: 56px; font-family: var(--serif); font-style: italic; font-size: 34px;
           color: var(--muted); }}
.url {{ color: var(--ink); }}
"""


def slide(out, name, body, hue):
    # each photographer gets a faint tint of their accent hue on the black, so the feed isn't monotone
    css = CSS.format(accent=f"hsl({hue} 40% 62%)", bg=f"hsl({hue} 14% 6%)",
                     hairline=f"hsl({hue} 12% 16%)", grain=GRAIN)
    out.write_text(
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        f'<link rel="stylesheet" href="{FONT}">'
        f"<style>{css}</style></head>"
        f"<body>{body}</body></html>", encoding="utf-8")


def main(slug):
    curator = slug == "curadoria"
    folder = SRC / slug
    meta, statement = parse_md((ROOT / "curadoria.md") if curator else folder / "info.md")
    site, _ = parse_md(ROOT / "index.md")
    name = meta["name"]
    e = html.escape
    head, _, last = e(name).rpartition(" ")
    h1 = f"{head} <em>{last}</em>" if head else e(name)
    title = e(site["title"])
    thead, _, tlast = title.rpartition(" ")
    title_h1 = f"{thead} <em>{tlast}</em>"

    folders = sorted(p.name for p in SRC.iterdir() if p.is_dir())
    hue = 15 if curator else 15 + folders.index(slug) * 360 // len(folders)  # base hue = homepage title accent

    kicker = f'<p class="kicker"><span>Exposição fotográfica</span><span>{title}</span></p>'
    bar = f'<p class="bar"><span>{e(site["period"])}</span><span>{e(site["venue"])}</span></p>'

    pf = [] if curator else sorted(f for f in (folder / "portfolio").glob("*") if f.suffix.lower() in IMG_EXTS)
    photos = pf[:6]  # 10-slide cap: 4 text slides + up to 6 photos

    paras = [p.strip() for p in statement.split("\n\n") if p.strip()]
    # instagram.md is the carousel script — "# Capa", "# Citação", "# Sobre",
    # "# Legenda" sections; heuristics below only fill in whatever is missing
    ig_md = folder / "instagram.md"
    ig_body = ig_md.read_text(encoding="utf-8") if not curator and ig_md.exists() else ""
    parts_ = re.split(r"^# +(.+)$", ig_body, flags=re.M)
    ig = {parts_[i].strip().lower(): parts_[i + 1].strip() for i in range(1, len(parts_) - 1, 2)}

    quoted = re.search(r'"([^"]+)"', statement)
    # no quoted line: pull the first paragraph that reads like a quote — skip bare
    # title lines (too short) and walls of text (too long)
    quote = ig.get("citação") or (quoted.group(1) if quoted else next(
        (p for p in paras if 40 <= len(p) <= 240), paras[0]))

    bio_md = folder / "bio.md"
    bio_paras = [p.strip() for p in bio_md.read_text(encoding="utf-8").split("\n\n") if p.strip()] if bio_md.exists() else []
    years = [p for p in bio_paras if re.match(r"Em \d{4}", p)]
    milestones = ([p.strip() for p in ig["sobre"].split("\n\n") if p.strip()] if "sobre" in ig
                  else years if len(years) >= 2 else [p for p in bio_paras if len(p) <= 240])[:3]

    def photo_slide(f, n):
        return (f'<div class="photo"><img src="{f.resolve().as_uri()}"></div>'
                f'<p class="caption"><em>{n:02d}</em>{e(name)}</p>')

    def rows(items):
        out = []
        for p in items:
            m = re.match(r"(?:Em (\d{4})|(Hoje)),?\s+(.*)", p, re.S)
            year, text = (m.group(1) or m.group(2), m.group(3)) if m else ("", p)
            out.append(f'<div><span class="year">{year}</span><p>{e(text)}</p></div>'
                       if year else f'<div><p>{e(p)}</p></div>')
        return "".join(out)

    def quoted_slide(text, sub):
        return (f'<div class="frame">{kicker}<div class="grow">'
                f'<p class="quote">“{e(text)}”</p>'
                f'<p class="label" style="margin-top:48px">{e(sub)}</p></div>{bar}</div>')

    def rows_slide(label, items):
        return (f'<div class="frame">{kicker}<div class="grow"><p class="label" style="margin-bottom:40px">'
                f'{label}</p><div class="milestones">{rows(items)}</div></div>{bar}</div>')

    role = '<p class="label" style="margin-bottom:32px">Curadoria</p>' if curator else ""
    h1_size = ' style="font-size:96px"' if curator else ""
    cover = (f'<div class="frame">{kicker}<div class="grow">{role}'
             f'<h1{h1_size}>{h1}</h1>'
             f'<p class="bio">{e(ig.get("capa") or meta.get("bio", ""))}</p></div>{bar}</div>')
    quote_slide = quoted_slide(quote, name)
    # a single "Sobre" paragraph reads as prose, not a timeline — style follows content
    sobre = (f'<div class="frame">{kicker}<div class="grow"><p class="label" style="margin-bottom:40px">'
             f'Sobre {e(name)}</p><p class="prose">{e(milestones[0])}</p></div>{bar}</div>'
             if len(milestones) == 1 else rows_slide(f"Sobre {e(name)}", milestones))
    invite = (f'<div class="frame">{kicker}<div class="grow"><p class="label" style="margin-bottom:32px">'
              f'Visite a mostra</p><h1 style="font-size:104px">{title_h1}</h1>'
              f'<p class="tagline">{e(site.get("tagline", ""))}</p>'
              f'<div class="details"><div><p class="label">Quando</p><p>{e(site["period"])}</p></div>'
              f'<div><p class="label">Onde</p><p>{e(site["venue"])}</p></div></div>'
              f'<p class="label" style="margin-top:72px"><span class="url">'
              f'{e(site["url"].removeprefix("https://"))}</span></p></div>'
              f'<p class="bar"><span>Curadoria</span><span>{e(site.get("curator", ""))}</span></p></div>')

    if curator:
        # curadoria.md body: lede, two exposition paragraphs, pull quote, thanks, two bio paragraphs
        lede, mostra, pull, thanks, bio_paras = paras[0], paras[1:3], paras[3], paras[4], paras[5:]
        roster = "".join(
            f'<div><span class="year" style="color:hsl({15 + i * 360 // len(folders)} 40% 62%); font-size:34px">'
            f'{i + 1:02d}</span><p class="rname">{e(parse_md(SRC / f / "info.md")[0]["name"])}</p></div>'
            for i, f in enumerate(folders))
        slides = [
            cover,
            quoted_slide(lede, name),
            rows_slide("A mostra", mostra),
            quoted_slide(pull.replace('"', ""), thanks),
            rows_slide(f"Sobre {e(name)}", bio_paras),
            f'<div class="frame">{kicker}<div class="grow"><p class="label" style="margin-bottom:24px">'
            f'{len(folders)} fotógrafos</p><div class="milestones roster">{roster}</div></div>{bar}</div>',
            invite,
        ]
    else:
        # photo-first: text slides breathe between pairs of photos, 10 slides max
        shots = [photo_slide(f, n) for n, f in enumerate(photos, 1)]
        slides = [cover] + shots[:2] + [quote_slide] + shots[2:4] + (
            [sobre] if milestones else []) + shots[4:] + [invite]

    out = ROOT / "promo" / slug
    out.mkdir(parents=True, exist_ok=True)
    for n, body in enumerate(slides, 1):
        page = out / f"slide-{n:02d}.html"
        slide(page, name, body, hue)
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--window-size=1080,1080",
             f"--screenshot={out / f'{n:02d}.png'}", page.resolve().as_uri()],
            check=True, capture_output=True)
        page.unlink()

    handle = meta.get("instagram", "").rstrip("/").rpartition("/")[2]
    caption = [ig["legenda"]] if "legenda" in ig else [p for p in [
        meta.get("description", ""),
        "",
        meta.get("bio", ""),
        "",
        f"Acompanhe: @{handle}" if handle else None,
        "" if handle else None,
        f"🗓 {site['period']} de 2026",
        f"📍 {site['venue']}",
        f"🔗 {site['url'].removeprefix('https://')}",
        "",
        "#OlharesCapixabas #FotografiaCapixaba #EspiritoSanto #Vitoria "
        "#Fotografia #ExposicaoFotografica #MostraFotografica",
    ] if p is not None]
    (out / "legenda.txt").write_text("\n".join(caption) + "\n", encoding="utf-8")
    print(f"ok: {len(slides)} slides + legenda in {out}")


if __name__ == "__main__":
    main(sys.argv[1])
