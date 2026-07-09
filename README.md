# Olhares Capixabas

Static website for **"Olhares Capixabas"**, a photography exposition by 12 photographers from Espírito Santo, Brazil, running August 1–30 at the Tribunal de Justiça do Espírito Santo (Vitória), curated by Profa. Katia Ludolf. Live domain: <https://mostraolharescapixabas.art.br>.

The site is intentionally minimal to operate: **markdown files in, plain HTML out**. There is no CMS, no framework, no npm — the only requirement is Python 3 (standard library only). You edit text files, run one script, and upload a folder of static files to any web host.

## How it works

`build.py` (~200 lines, zero dependencies) reads the content files and generates the whole site into `dist/`:

```
index.md                      → dist/index.html            (homepage)
agradecimentos.md             → dist/agradecimentos/       (any root .md becomes a page)
photographers/<slug>/info.md  → dist/<slug>/               (one page per photographer)
photographers/<slug>/*.jpg    → copied next to the page
style.css                     → copied as-is
                              → dist/sitemap.xml, dist/robots.txt
```

Frontmatter is plain `key: value` lines between `---` markers, parsed by hand — no YAML library. Page bodies are plain paragraphs separated by blank lines (no markdown syntax rendering; it has not been needed).

## Editing content

**Homepage — `index.md`.** Frontmatter keys: `title`, `period`, `tagline`, `venue`, `address`, `curator`, `url`. The body is an optional introduction text. The `url` key enables canonical URLs, `og:image`, sitemap and robots.txt — remove it and those disappear, nothing breaks.

**Photographers — `photographers/<slug>/info.md`.** The folder name becomes the URL. Frontmatter: `name`, `bio`, and *any other key becomes a link* (`instagram: https://…` renders as an "instagram" link; values containing `@` get `mailto:` automatically). The body is the series statement: the first paragraph renders as a large italic lede, the following paragraphs as smaller body text — statements can be long.

Photos live in the same folder (`.jpg`, `.png`, `.webp`, `.gif`, `.avif`, `.svg`) and appear in alphabetical order — prefix with `01-`, `02-` to control it. The current SVG files are placeholders; replace them with real photographs.

**Standalone pages.** Any `.md` in the project root (besides `index.md`/`README.md`) becomes `/<filename>/`, with `title` frontmatter, and is linked automatically from the homepage footer. `agradecimentos.md` (acknowledgements) is the existing example.

**All content is currently fake** — the 12 photographers, their bios, statements, links and emails are invented examples demonstrating the format.

## Build & preview

```sh
python3 build.py                  # regenerates dist/ from scratch
python3 -m http.server -d dist    # preview at http://localhost:8000
```

The edit loop is: change a file → `python3 build.py` → refresh the browser. To deploy, upload the **contents of `dist/`** to the host; `dist/` is gitignored because it is fully derived.

## Design

Black editorial theme inspired by gallery/print design: near-black background, warm off-white ink, [Fraunces](https://fonts.google.com/specimen/Fraunces) display serif (the site's only external resource, loaded from Google Fonts with a graceful serif fallback), and tiny uppercase letterspaced labels used as "metadata" throughout. Titles and names get an automatic italic accent on the last word ("Olhares *Capixabas*"). Each photographer also gets an accent color (12 evenly-spaced hues, assigned by folder order in `build.py`) used sparingly — roster number, hover, italic surname, figure captions — and the homepage kicker rule is a thin strip of all twelve, one band per voice in the show.

The homepage is a poster: oversized title with the curator credit at its baseline, a Quando/Onde info band (address linked to Google Maps), and a numbered photographer roster with hairline rules. Photographer pages set the statement lede large, then run the gallery in a repeating asymmetric rhythm — full-width, large-left, smaller-right-offset — with numbered captions. Portrait images are capped at 85vh. There is **no JavaScript**; all interaction is CSS. Everything collapses to a single column on narrow screens.

## SEO

Every page gets a meta description (derived from the statement lede / tagline / page excerpt), Open Graph tags, and a Twitter card (`summary_large_image` when a photo is available). With `url:` set, pages also get canonical URLs and `og:image`, and the build emits `sitemap.xml` + `robots.txt`.

## Conventions

- Source code, comments and program messages in English; site content in Portuguese.
- Commit messages in English, [Conventional Commits](https://www.conventionalcommits.org/) style.
