# API Proxy Guide

This document describes the external API contract of the read-only proxy service used by OpenClaw.

Base URL example:

`https://fintablo-proxy.example.com`

## Endpoint mapping (short)

| Proxy endpoint | Upstream Fintablo endpoint | Notes |
|---|---|---|
| `GET /accounts` | `GET /v1/moneybag` | Accounts list |
| `GET /transactions` | `GET /v1/transaction` | Query params are normalized and mapped |
| `GET /balances` | `GET /v1/moneybag` | Local filtering by `account_id` and optional `date` cutoff |
| `GET /cashflow` | `GET /v1/transaction` | Proxy paginates and aggregates totals by group |
| `GET /categories` | `GET /v1/category` | Categories list |
| `GET /health` | none | Local healthcheck only |

## Authentication

All business endpoints require:

`X-API-Key: <OPENCLAW_PROXY_API_KEY>`

If key is missing or invalid:

- Status: `401`
- Body:

```json
{"detail":"Unauthorized"}
```

## Security model

- Only allowlisted routes are exposed.
- Only `GET` methods are implemented for proxy endpoints.
- Write methods (`POST`, `PUT`, `PATCH`, `DELETE`) return `405 Method Not Allowed`.
- Upstream Fintablo token is stored server-side only and never returned to clients.
- Optional source IP restriction is enforced via `ALLOWED_CLIENT_IPS`.

## Endpoints

## `GET /health`

Healthcheck endpoint.

- Auth required: No
- Upstream call: No
- Response `200`:

```json
{"status":"ok"}
```

## `GET /accounts`

Returns accounts list from upstream Fintablo.

- Auth required: Yes
- Upstream mapping: `GET /v1/moneybag`

Example:

```bash
curl -s -H "X-API-Key: <KEY>" "https://fintablo-proxy.example.com/accounts"
```

## `GET /transactions`

Returns transaction list with read-only filtering options.

Query params:

- `date_from` (optional, `YYYY-MM-DD`)
- `date_to` (optional, `YYYY-MM-DD`)
- `account_id` (optional, string)
- `limit` (optional, default `100`, max `500`)
- `offset` (optional, default `0`)

Auth required: Yes

Upstream mapping:

- `date_from` -> `dateFrom` (`DD.MM.YYYY`)
- `date_to` -> `dateTo` (`DD.MM.YYYY`)
- `account_id` -> `moneybagId`
- `limit` -> `pageSize`
- `offset` -> `page` (computed as `(offset // limit) + 1`)

Example:

```bash
curl -s -H "X-API-Key: <KEY>" \
  "https://fintablo-proxy.example.com/transactions?date_from=2026-01-01&date_to=2026-01-31&limit=100&offset=0"
```

## `GET /balances`

Returns balances data from accounts source. If `account_id` is set, items are filtered by account id in proxy.

Query params:

- `date` (optional, `YYYY-MM-DD`; applied as local cutoff by `surplusTimestamp`)
- `account_id` (optional, string)

Auth required: Yes

Upstream mapping: `GET /v1/moneybag`

## `GET /cashflow`

Returns aggregated cashflow totals for the period.

Query params:

- `date_from` (required, `YYYY-MM-DD`)
- `date_to` (required, `YYYY-MM-DD`)

Auth required: Yes

Upstream mapping: `GET /v1/transaction` with converted dates and paging (`pageSize=1000`, `page=1..N`), then aggregation by `group`:

- `income`
- `outcome`
- `transfer`

## `GET /categories`

Returns categories list.

- Auth required: Yes
- Upstream mapping: `GET /v1/category`

Example:

```bash
curl -s -H "X-API-Key: <KEY>" "https://fintablo-proxy.example.com/categories"
```

## Error contract

Upstream errors are normalized to safe response:

- Status: `502`
- Body:

```json
{"detail":"Upstream service error","status_code":502}
```

## Relation to original Fintablo docs

The proxy exposes a restricted external contract.  
Use this file as the source of truth for OpenClaw integration.

Original Fintablo Swagger can be used internally only to understand upstream semantics and field-level details.
