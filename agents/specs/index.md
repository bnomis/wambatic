# Spec Index

| Spec | Path | Description |
|------|------|-------------|
| [System](system/spec.md) | `src/wambatic/` | Architecture, data flow, stack, build order and settings across components |
| [Fetch](fetch/spec.md) | `src/wambatic/fetch/` | GitHub GraphQL/REST clients, auth, rate limits, incremental sync |
| [Cache](cache/spec.md) | `src/wambatic/fetch/cache.py` | SQLite cache: schema, sync state, ETags, identity checks |
| [Stats](stats/spec.md) | `src/wambatic/stats/` | Metric computation, time bucketing, subjects (user, repo, org) |
| [Reports](reports/spec.md) | `src/wambatic/reports/`, `src/wambatic/cli.py` | Terminal, static HTML and local web app front ends |
| [User guide](user-guide/spec.md) | `docs/`, `mkdocs.yml`, `bin/screenshots.py` | MkDocs Material user guide on GitHub Pages, with diagrams, screenshots and a drift test |

Read the system spec first. Each component spec lists its prerequisites.

Sequencing of the work is in [Implementation order](implementation-order.md).
