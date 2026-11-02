# Spec Index

| Spec | Path | Description |
|------|------|-------------|
| [System](system/spec.md) | `src/wambatic/` | Architecture, data flow, stack, build order and settings across components |
| [Fetch](fetch/spec.md) | `src/wambatic/fetch/` | GitHub GraphQL/REST clients, auth, rate limits, incremental sync |
| [Commit sync](commit-sync/spec.md) | `src/wambatic/fetch/git.py` | Commits from local bare clones: per-file line counts, followed branches, rewrite detection |
| [Cache](cache/spec.md) | `src/wambatic/fetch/cache.py` | SQLite cache: schema, sync state, ETags, identity checks |
| [Stats](stats/spec.md) | `src/wambatic/stats/` | Metric computation, time bucketing, subjects (user, repo, org) |
| [Metric groups](metric-groups/spec.md) | `src/wambatic/stats/activity.py`, `flow.py`, `delivery.py`, `popularity.py` | What each metric group counts: series, units, order and tables |
| [Reports](reports/spec.md) | `src/wambatic/reports/` | What the front ends share: layout, errors, JSON output, `service.py`, settings |
| [CLI](cli/spec.md) | `src/wambatic/cli.py`, `src/wambatic/__main__.py` | The `wambatic` command line, its flags and exit statuses |
| [Terminal report](terminal-report/spec.md) | `src/wambatic/reports/terminal.py`, `rows.py` | The `rich` terminal report and the shared table rows |
| [HTML report](html-report/spec.md) | `src/wambatic/reports/figures.py`, `html.py` | The self-contained static HTML report, its figures and themes |
| [Web app](web-app/spec.md) | `src/wambatic/reports/web.py` | The local web app: routes, sync jobs, security |
| [User guide](user-guide/spec.md) | `docs/`, `mkdocs.yml`, `bin/screenshots.py` | MkDocs Material user guide on GitHub Pages, with diagrams, screenshots and a drift test |

Read the system spec first. Each component spec lists its prerequisites.

Sequencing of the work is in [Implementation order](implementation-order.md).
