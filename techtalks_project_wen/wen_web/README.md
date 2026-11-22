# wen_web: the Wen frontend

Server-rendered Django templates with HTMX, Alpine.js and Leaflet, as in the project brief.
No build step and no Node: every library is vendored under `static/wen/vendor/`.

## Run it

From the repository root, with `techtalks_project_wen/.env.dev` in place:

```bash
docker compose --env-file techtalks_project_wen/.env.dev -f techtalks_project_wen/docker-compose.yml up --build -d
docker compose --env-file techtalks_project_wen/.env.dev -f techtalks_project_wen/docker-compose.yml exec web python manage.py migrate
```

Open http://localhost:8000. Create an account from **Get started**.
Password-reset emails are printed in the `web` container logs while `DEBUG=1`.

Tests (15, covering the resolver, the full create, share, drive, deliver flow, privacy and Arabic):

```bash
docker compose --env-file techtalks_project_wen/.env.dev -f techtalks_project_wen/docker-compose.yml exec web python manage.py test
```

Run `manage.py test` with no label. With the `wen_web` label, Django imports the app twice under two names.

## What is real and what is simulated

| Part | Status |
| --- | --- |
| Accounts: register, log in, log out, password reset | Real (`django.contrib.auth`, stored in PostgreSQL) |
| Pages, forms, validation, share links, expiry, driver flow | Real logic, implemented in this app |
| Landmark resolution | **Simulated**: `services/mock_resolver.py` over ~20 hand-made landmarks (`services/gazetteer.py`) |
| Address storage | **Simulated**: one JSON file plus uploads in `media/wen_dev/` (git-ignored) |

The UI says so wherever it matters: a "Development data" note in the app sidebar,
and "Simulated resolver" next to every resolution result. Nothing claims to be connected to OpenStreetMap or Photon yet.

## How it fits together

```
views/ ──► services.get_resolver()    ──► MockLandmarkResolver   (lane 1 replaces)
       └─► services.get_repository()  ──► JsonFileAddressRepository (platform lane replaces)
templates/wen/   layouts, components (address card, link panel...), pages
static/wen/css/  tokens.css → base.css → components.css → layout.css → pages.css
static/wen/js/   main.js registers Alpine components; core/api.js is the only place that calls fetch()
```

Views never touch storage directly. To plug in the real backend:

1. Implement `LandmarkResolver` and/or `AddressRepository` from `services/base.py`.
   The data shapes are in `services/types.py`, and they are the contract the templates rely on.
2. Return your class from `get_resolver()` / `get_repository()` in `services/__init__.py`
   for a new `WEN_SERVICE_BACKEND` value, and set that value in `.env.dev`.

Backend pieces the UI is ready for:

- `resolve(text)`: candidates with `quality` (strong / partial / weak) and `matched_text`, plus `hints` (floor, colour). Called through `POST /ui-api/resolve/`.
- Address cards with entrance photos and an optional voice note, owner-scoped.
- Share links: unguessable token, chosen lifetime (24 h, 3, 7 or 30 days), replaced on re-issue, ended on revoke or delivery.
- Events: `created`, `link_created`, `link_opened`, `landmark_confirmed`, `landmark_rejected`, `delivered`, `link_revoked`. Insights are computed only from these.

## Pages

| URL | Page |
| --- | --- |
| `/` | Landing page with a live demo of the resolver |
| `/accounts/login/`, `register/`, `password-reset/`… | Authentication |
| `/app/` | Dashboard |
| `/app/addresses/` | Saved addresses (live search, filters, sort) |
| `/app/addresses/new/` | Create: describe, confirm landmark, details, then share |
| `/app/addresses/<id>/` | Card preview, private link, activity |
| `/app/insights/` | Delivery insights for businesses |
| `/c/<token>/` | The address card a driver or guest opens (no login) |
| `/c/<token>/drive/` | Driver mode |

## Privacy rules the frontend follows

- Cards are owner-only. Every owner URL returns 404 for anyone else.
- Photos and voice notes are never public files. They are streamed through views that check the owner, or an active token.
- Share pages send `noindex`, `no-store` and `Referrer-Policy: same-origin`, so the token never leaks to Google Maps or WhatsApp.
- A delivered, expired or revoked link shows nothing about the address.
- Nothing about an address is kept in `localStorage`.

## Arabic

The interface is fully translated (`locale/ar/LC_MESSAGES/django.po`), with right-to-left layouts.
All CSS uses logical properties (`margin-inline-start`…), so it mirrors without extra rules. Maps stay left-to-right on purpose.
User text uses `dir="auto"` so Arabic, Arabizi and English all display correctly.

After changing a string, update the `.po` and recompile (needs GNU gettext, e.g. `apt-get install gettext` in the container):

```bash
python manage.py makemessages -l ar --ignore "media/*"
python manage.py compilemessages
```

The compiled `django.mo` is committed (see the `.gitignore` exception) so the app works without gettext installed.

## Design system

- Typeface: **Readex Pro** (OFL), one family for Arabic and Latin. It was designed for both scripts, and one of its designers is Lebanese. Headings use its width axis (`HEXP`).
- Colour: ink navy `#10243a` for text and primary actions, sea `#0b6e85` as the accent. Green, amber and red are used only for meaning (confirmed, uncertain, error).
- Signature element: the dashed *route* (`.route` in components.css), which draws a description as a chain from landmark to door.
- Map tiles: CARTO Voyager over OpenStreetMap data, set with `WEN_MAP_TILE_URL`. Attribution is shown on every map.
