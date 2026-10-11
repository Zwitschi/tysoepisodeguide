# Frontend Review & Refactor Plan

## Current state (review)

The main page (`templates/index.html`, served by `app.py` `index()`) renders the
full episode list server-side:

- `index()` loads **all** episodes (`get_videos(order)` → 381 rows) and passes
  them to Jinja every request.
- Two display modes via `?view=table|thumbs` (`set_view_mode`).
- Sort order via `?sort=ASC|DESC` (`sort_order`), applied by publish date.
- `?limit=N` only affects the thumbnails view (`episodes[:limit]`).

### Issues found

1. **Missing header** — `index.html` overrode the `header` block with an empty
   block, hiding the site title and navigation on the main page. **Fixed.**
2. **No pagination** — the whole table (381 rows) is rendered at once; there is
   no page-size control.
3. **Sort link drops state** — the column sort link only passes `?sort=…`,
   losing `view` and `limit`.
4. **Static rendering** — episode list/details are rendered with Jinja rather
   than fetched from the JSON API (`/api/*`).
5. **Hardcoded thumbnail path** — templates use `/thumbs/<id>.jpg` directly
   instead of the thumbnail URL stored in the DB.

## Proposed architecture

Move the data-driven pages to the JSON API and render client-side:

```txt
Browser → JS fetch /api/episodes?limit=20&offset=0 → render table/grid
       → JS fetch /api/episodes/<id>              → render episode detail
       → JS fetch /api/guests, /api/guests/<name> → render guest pages
```

Server-side keeps only:

- The shell pages (`index.html`, `episode.html`, `guests.html`, `guest.html`)
  with SEO meta tags.
- The JSON API endpoints already implemented in `app.py`.

### Benefits

- Single source of truth (the API) for both the web app and any future clients.
- Pagination can be added without re-rendering the whole page.
- Smaller HTML payloads; episodes load on demand.

## Pagination plan (main episode list)

Defaults and controls:

| Parameter | Values                   | Default |
| --------- | ------------------------ | ------- |
| `limit`   | 20, 50, 100, 500, 1000   | 20      |
| `offset`  | non-negative int         | 0       |

The API already supports `limit` and `offset` (`GET /api/episodes?limit=&offset=`),
and returns `count`, `offset`, `limit`, and the page of episodes.

UI:

- A `<select>` above the table with options **20 / 50 / 100 / 500 / 1000**.
- **Previous / Next** buttons (disabled at the ends), plus a simple
  "Showing X–Y of Z episodes" label.
- Preserve `sort` and `view` across pagination.
- When the page size changes, reset `offset` to 0.

## Episode detail page refactor

- Replace the server-rendered `Episode` object with a client-side fetch of
  `GET /api/episodes/<id>`.
- Keep the YouTube iframe, description, and guest links; populate them from the
  JSON response (`title`, `formatted_date`, `formatted_description`,
  `guest`, `url`).
- The API already returns `formatted_date` and `formatted_description`, so the
  rendering logic can move to JS without changes to `Episode`.

## Guest pages refactor

- `GET /api/guests` returns `{name, episode_count}`; render the guest table from
  this (avoids building every `Episode` object server-side on each request).
- `GET /api/guests/<name>` returns the guest and their episodes; use it for the
  guest detail page.
- Guest names contain spaces/special chars (`&`, `'`); URLs must be encoded with
  `encodeURIComponent` when calling the API.

## Visual style — align with rickglassman.com

Inspect the current live site (<https://rickglassman.com/>) and adopt its main-page
look in our CSS.

### Findings (inspected 2026-10-11)

The live site is a Nuxt 3 app. Computed styles on the homepage:

- **Body font**: `"DM Sans", sans-serif`
- **Navigation font**: `"Dela Gothic One", sans-serif`
- **Headings**: `Anton` (display face)
- **Body background**: `rgb(240, 235, 224)` → `#F0EBE0` (cream)
- **Body text**: `rgb(17, 17, 17)` → `#111111` (near-black)

Fonts are self-hosted in `/_nuxt/` (declared via `@font-face` in
`entry.*.css`). Latin subset files:

| Font | Weight | URL |
| ---- | ------ | --- |
| Anton | 400 | `https://rickglassman.com/_nuxt/Anton-normal-400-latin.Byf51wtH.woff2` |
| DM Sans | 400 | `https://rickglassman.com/_nuxt/DM_Sans-normal-400-latin.Xz1IZZA0.woff2` |
| Dela Gothic One | 400 | `https://rickglassman.com/_nuxt/Dela_Gothic_One-normal-400-latin.AgyGD05y.woff2` |
| Space Grotesk | 500 | `https://rickglassman.com/_nuxt/Space_Grotesk-normal-500-latin.BhU9QXUp.woff2` |

(DM Sans 500/700 are also used on the site.)

### Applied (2026-10-11)

1. ✅ Downloaded the four latin `.woff2` files into `static/fonts/`.
2. ✅ Replaced the `amboy-black` `@font-face` with `Anton`, `DM Sans`,
   `Dela Gothic One`, and `Space Grotesk` in `static/css/style.css`.
3. ✅ Updated `style.css` to use the new fonts (`DM Sans` body, `Anton`
   headings, `Dela Gothic One` nav) with a dark background (`#111`) and cream
   text (`#F0EBE0`) as the default.
4. ✅ Restyled the header/nav, episode table, and footer; tables use the dark
   Bootstrap variant on the dark background.
5. ✅ Verified locally — pages render with the new fonts and palette
   (fonts are self-hosted, no network dependency).

Note: `Space Grotesk` is downloaded but not yet used by any rule; it is
available for future accents.

## Suggested implementation order

1. Main page: server keeps initial render, add client-side pagination controls
   that call `/api/episodes`.
2. Episode detail: fetch `/api/episodes/<id>` and render with JS.
3. Guest list & detail: fetch `/api/guests` and `/api/guests/<name>`.
4. Remove now-unused server-side helpers (`get_videos`, `get_guest_list`, etc.)
   once no template depends on them.
