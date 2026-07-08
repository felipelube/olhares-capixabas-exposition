# Olhares Capixabas

Site estático da exposição. Sem dependências — só Python 3.

## Conteúdo

Tudo é arquivo `.md` com frontmatter (bloco `chave: valor` entre `---`).

**Páginas avulsas** — qualquer `.md` na raiz (além de `index.md` e `README.md`) vira uma página em `/<nome-do-arquivo>/`, com link automático na barra do topo da homepage. Frontmatter: `title`. Ex.: `agradecimentos.md`.

**Homepage** — `index.md`: `title`, `period` e `tagline` no frontmatter; o corpo do arquivo é o texto de apresentação (opcional, pode ficar vazio).

**Fotógrafo** — pasta em `photographers/nome-da-pessoa/` (o nome da pasta vira a URL) com um `info.md`:

- Frontmatter: `name`, `bio` e qualquer outra chave vira link (`instagram: https://...` → link "Instagram"; `email: pessoa@dominio.com` vira link mailto automaticamente).
- Corpo: o statement da série. Linha em branco separa parágrafos. O primeiro parágrafo aparece em destaque (itálico, grande); os seguintes em texto menor — pode ser longo.
- As fotos ficam na mesma pasta (`.jpg`, `.png`, `.webp`...), em ordem alfabética — prefixe com `01-`, `02-` para controlar a ordem.

Copie qualquer pasta existente para começar.

## Build

```sh
python3 build.py
```

Gera tudo em `dist/`. Suba o conteúdo de `dist/` para o servidor.

Para ver localmente: `python3 -m http.server -d dist` e abra http://localhost:8000
