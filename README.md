# Bricolage — a Micro.blog / Hugo theme

A warm, editorial **field-notebook** theme. One typed stream (links, photos,
books, videos, notes, essays) with a sticky **Now** panel, plus bespoke
category pages for **Photos, Books, Games and Pigeons**. Spectral serif +
JetBrains Mono, the Warm Burnout material palette, a solid terra-cotta strip,
and full light / dark.

> Built to Micro.blog's plug-in/theme conventions. Test on a staging blog
> before pointing your live site at it. The Unsplash URLs in `config.json` are
> placeholders — swap in your own.

---

## Install

### On Micro.blog (recommended)
A custom theme on Micro.blog is a **plug-in**.

1. Push this folder to a public GitHub repo.
2. In Micro.blog: **Design → Edit Custom Themes → New Theme**, or use **Plug-ins →
   install via Clone URL** and paste the repo URL.
3. Select Bricolage as your blog's theme.
4. Set the Hugo version: **Design → Hugo Version → 0.91 or newer** (the templates
   use `urls.Parse`, `findRE`, taxonomy iteration; all fine on 0.91+).

Because it ships every template, nothing falls back to the built-in design.

### Locally with Hugo
```
your-site/
  themes/bricolage/      ← this folder
  config.toml            ← theme = "bricolage"
  content/...
hugo server
```

---

## One-time setup

**Create the categories** (Posts → Categories): `Photos`, `Books`, `Games`,
`Pigeons`. Micro.blog auto-assigns *Photos* to photo posts. Category pages live
at `/categories/<name>/`.

**Navigation.** The header renders your **main menu** if you have one; otherwise
it auto-lists your categories + Archive + About. Point menu items at
`/categories/photos/`, `/categories/books/`, etc.

---

## The "Now" panel = one source of truth

The homepage **Now** widget *and* the "Now Reading" / "Now Playing" heroes on the
Books and Games pages all read from `config.json → params.now`. Edit it once:

```json
"now": {
  "reading": { "title": "...", "author": "...", "cover": "https://...",
               "note": "...", "started": "Feb 22", "progress": 38 },
  "playing": { "title": "...", "platform": "PS5", "tag": "co-op", "hours": 14,
               "art": "https://...", "note": "..." },
  "activity": { "title": "Pigeons", "meta": "always pigeons" }
}
```
`params.elsewhere` (the social links) and `params.about` live in the same file.

---

## How post types are detected

The stream renders each post by an inferred type — no manual tagging needed:

| Type   | Detected when…                                  | Kicker   |
|--------|-------------------------------------------------|----------|
| Link   | front matter has `externalurl`                  | `Link`   |
| Book   | front matter has `book: true` (or in Books cat) | `Reading`|
| Photo  | post has `photos`/`images` (Micro.blog adds these) | `Photo` |
| Watch  | content embeds YouTube/Vimeo                    | `Watch`  |
| Essay  | post has a title (and none of the above)        | `Essay`  |
| Note   | a title-less micropost                          | `Note`   |

## Front-matter conventions

**Link post**
```yaml
externalurl: "https://example.com/article"
title: "Optional headline"
```

**Book** (post in the `Books` category)
```yaml
title: "Piranesi"
author: "Susanna Clarke"
cover: "https://.../cover.jpg"     # or attach a photo
status: "Finished"                  # Reading | Finished | Abandoned
rating: 5                           # 0–5, optional
# body = your note
```

**Game** (post in the `Games` category)
```yaml
title: "Pentiment"
platform: "PC"
status: "Beaten"                    # Beaten | Shelved | Endless/Playing
steam: "https://store.steampowered.com/app/1205520/"   # optional → links the title + a Steam icon
# body = your one-line note
```
The "Now Playing" hero takes a `steam:` URL too (`config.json → now.playing.steam`).

**Pigeon** (post in the `Pigeons` category)
```yaml
title: "Suspicious of me"           # used as the caption
location: "Bryant Park"             # optional
# attach one photo
```

**Photo** — just attach photo(s); Micro.blog sets the `photos` param.

---

## File map

```
config.json                     site + Now/elsewhere params
theme.toml / plugin.json        theme metadata for Micro.blog
layouts/
  _default/baseof.html          page shell
  index.html                    home — typed stream + Now + pagination
  _default/single.html          one post
  _default/list.html            Archive (year groups) + /categories/ index
  _default/term.html            category pages → Photos/Books/Games/Pigeons
  partials/
    head.html  header.html  footer.html
    now.html              the Now panel
    stream-item.html      one typed stream card
    icons.html            inline SVGs
static/
  css/bricolage.css       the whole look (responsive, light/dark)
  js/theme.js             light/dark toggle (persisted) + mobile nav
_preview.html             local static preview (not used by Hugo — safe to delete)
```

## Light / dark
Defaults to the visitor's system preference; the header toggle overrides it and
remembers the choice (`localStorage`). A pre-paint script in `head.html` applies
the saved choice with no flash.

## Notes
- Custom CSS you add in Micro.blog (Design → Edit CSS) loads **after** the theme,
  so it always wins.
- Plug-in CSS/JS hooks (`plugins_css`, `plugins_js`) are wired in head/footer.
- Conversation replies render on post pages when that Micro.blog design setting
  is on.
