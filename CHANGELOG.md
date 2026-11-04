# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] — 2026-11-04

### Added

- Thumbnail show/hide toggle on the episode list (button above the table,
  default hidden, state persisted via `?thumbs=1|0` URL parameter)
- `MissingAPIKeyError` with an actionable message when the YouTube API key is
  not configured (friendly CLI error, clear SSE message, startup warning)
- Friendly 404/500 error pages (`templates/notfound.html`); `/api/*` routes
  return JSON errors instead of HTML

### Security

- Fixed SQL injection in `Videos.read()` (parameterized query) and hardened
  `Videos.read_videos()` sort-direction handling (whitelisted inside the class)

### Changed

- Episode thumbnails now load directly from the YouTube CDN (`i.ytimg.com`)
  instead of self-hosted copies in `static/thumbs/`

### Removed

- Self-hosted thumbnail pipeline: `classes/thumbnail.py`, thumbnail
  download/resize logic in `setup.py`, `thumbnails` CLI action, `/images`
  endpoint, `preloader.js`, and the `pillow` dependency
- 1102 cached thumbnail files removed from version control

## [3.0.0] — 2026-10-11

### Changed

- Refactored YouTube fetching to use `playlistItems` pagination and a quota-aware
  client with token-bucket rate limiting (`utils/youtube.py`) (#1e638c5)
- Avoid logging API response bodies (#cba69fa)
- Updated database, prepared v3 release (#4b3277c)

### Removed

- Legacy YouTube API wrapper `classes/youtubeapi.py` (unused) (#92e0ff4)
- Legacy timing helper `utils/timing.py` (unused) (#92e0ff4)

### Added

- JSON API endpoints: `GET /api/episodes`, `GET /api/episodes/<id>`,
  `GET /api/guests`, `GET /api/guests/<name>` (#ccbd0b3)
- Pagination on the main episode list (per-page selector: 25/50/100/500/1000,
  previous/next controls) (#ccbd0b3)
- Frontend restyle aligned with rickglassman.com (fonts, colors) (#ccbd0b3)

### Fixed

- Restored missing header on the main page (`index.html` had overridden the
  header block with an empty block) (#ccbd0b3)

## [2.1.0] — 2026-01-18

### Added

- View mode (`?view=table|thumbs`) and limit functionality to the index route (#7c60d30)

### Changed

- Refactored HTML structure in base and index templates for readability (#0536ccd)
- Refactored guest list method to use `Optional` type hint (#15aed9b)
- Updated episode thumbnails and index template layout (#877fa2d)
- Database update (#ea7ce98)

## [2.0.0] — 2025-09-18

### Changed

- Enhanced application functionality and updated dependencies (#f9f028b)
- Database update (#795d5de)

## [1.5.0] — 2025-06-25

### Security

- Updated Jinja2, requests, and urllib3 versions in requirements (#7aa1fd4)
- Removed compression (#2bbd879)

### Changed

- Database update (#2bbd879)

## [1.4.0] — 2025-01-13

### Fixed

- Refactored episode guest class with specific functions extending the mapping
  dict (#ec49964)
- Added episode guest exceptions (#9a9a582)

## [1.3.0] — 2024-12-24

### Security

- Bump jinja2 from 3.1.4 to 3.1.5 (dependabot) (#fe41473)
- Bump werkzeug from 3.0.4 to 3.0.6 (dependabot) (#411f798)

## [1.2.0] — 2024-09-27

### Added

- Sitemap via `flask_sitemapper` (#42e5a42)

### Fixed

- Date format in sitemap (#8b5f3da)
- Episode URL construction (use `episode.url`) (#e4f6c54, #3aad8c2)
- Updated GitHub Actions workflow to latest version (#9e6eff5, #f6cd6fd, #2be9294)

### Changed

- Updated README (#2c56358)

## [1.1.0] — 2024-05-27

### Fixed

- Typo in episode guest mapping (#af7de23)
- Guests listing for episode 122 (#14e5d36)

### Changed

- Database update (#1dac628)
- Image preloader updated (#601877d)

## [1.0.0] — 2024-03-17

### Added

- Reworked app with database-backed episode guide (#5306f91)
- Azure App Service deployment workflow (#6e95e6d)
- `/update` route and setup pipeline (#578cac6, #2361812)
- Classes architecture (`classes/`), docstrings (#1e2c285, #40a594c)
- Waitress/WSGI server for deployment (#7ffd308, #f1e6a48, #aa3f1a0)
- `.env` handling for deployment (#b594693, #a84dcb5)

### Fixed

- Video link fix (#616cf99)
- Exception for Whitney Cummings guest mapping (#342a8ae)
- Update URL fix (#0883e60)

### Changed

- Sorting, layout changes, extended README and ABOUT (#36f2821)
- Database updates (#332c91a, #7cfd7b5, #a6c8058, #0792b1e)
- Template updates and restructure (#3484edf, #0792b1e)
- New thumbnails, updated setup (#d7b757d)

## [0.1.0] — 2023-07-08

### Added

- Initial commit: repository setup with ABOUT, README, LICENSE (#499c52a)
- Setup pipeline (`setup.py`) for database creation and updates (#a5fde82, #727514e)
- Azure App Service build and deployment workflow (#6e95e6d)
- Database layer (formerly ignored) (#d9bdedb)
- Sorting and layout changes (#36f2821)

[Unreleased]: https://github.com/Zwitschi/tysoepisodeguide/compare/v3.1.0...HEAD
[3.1.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/v2.0.0...v3.1.0
[3.0.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/v2.0.0...92e0ff4
[2.1.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/v2.0.0...ea7ce98
[2.0.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/634f2d1...ebb45d7
[1.5.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/297a5ae...d8bf6d2
[1.4.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/5f87eab...297a5ae
[1.3.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/b665aee...5f87eab
[1.2.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/94e87b1...8b5f3da
[1.1.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/a5a4dfd...1dac628
[1.0.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/499c52a...601877d
[0.1.0]: https://github.com/Zwitschi/tysoepisodeguide/compare/499c52a...36f2821
