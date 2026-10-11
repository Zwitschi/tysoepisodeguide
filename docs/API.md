# JSON API

The Flask app exposes a small JSON API for the TYSO episode guide. All responses
are `application/json`.

Base URL: `/api`

## Endpoints

| Method | Route                        | Description                                        |
| ------ | ---------------------------- | -------------------------------------------------- |
| GET    | `/api/episodes`              | List episodes (paginated)                          |
| GET    | `/api/episodes/<episode_id>` | Episode details by YouTube video id                |
| GET    | `/api/guests`                | List all guests with their episode counts          |
| GET    | `/api/guests/<guest_name>`   | Guest details and the list of their episodes       |

## Query parameters

`/api/episodes` and `/api/guests` accept:

| Parameter | Values            | Default | Description                              |
| --------- | ----------------- | ------- | ---------------------------------------- |
| `sort`    | `ASC` or `DESC`   | `ASC`   | Sort order (by publish date)             |
| `limit`   | non-negative int  | `20`    | Max items per page (`0` returns all)     |
| `offset`  | non-negative int  | `0`     | Number of items to skip (pagination)     |

## Response shapes

### `GET /api/episodes`

```json
{
  "count": 380,
  "offset": 0,
  "limit": 20,
  "episodes": [
    {
      "id": "video-id",
      "title": "...",
      "url": "https://www.youtube.com/watch?v=video-id",
      "description": "...",
      "thumb": "https://...jpg",
      "duration": 6001,
      "number": "1",
      "formatted_date": "2019-04-22",
      "formatted_description": "...",
      "guest": ["Jon DeWalt"]
    }
  ]
}
```

### `GET /api/episodes/<episode_id>`

Returns a single episode object (same shape as the list items). Returns
`{"error": "Episode not found"}` with status `404` when the id is unknown.

### `GET /api/guests`

```json
{
  "count": 123,
  "guests": [
    { "name": "Adam Ray", "episode_count": 12 }
  ]
}
```

### `GET /api/guests/<guest_name>`

```json
{
  "name": "Adam Ray",
  "episodes": [ { "...episode object..." } ]
}
```

Returns `{"error": "Guest not found"}` with status `404` when the guest is unknown.

## Notes

- Episode lists are sorted by publish date (matching the main page), not by
  episode number, because episode numbers are stored as text and include
  decimals (e.g. `56.1`).
- Errors are returned with an appropriate HTTP status and a JSON `error` field.
