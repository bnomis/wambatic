# User guide

**Version:** 1.0
**Status:** implemented
**Date:** 2026-11-01

A user guide for wambatic: an [MkDocs](https://www.mkdocs.org/) site in the
[Material](https://squidfunk.github.io/mkdocs-material/) theme, built from `docs/` and published to
GitHub Pages at <https://bnomis.github.io/wambatic/>. It follows the metafopy guide's style: the same
theme colours and fonts, a home page that leads with a working example, task pages under "User guide",
and reference pages. It shows more than it tells. Each page uses a [Mermaid](https://mermaid.js.org/)
diagram where a flow, a state or a structure is being explained, and a screenshot wherever there is
output to look at.

**Audience.** An experienced git user who has not used the GitHub APIs. The guide assumes `git`, a
shell and a terminal. It explains, and links to the primary source for, everything else it relies on:
GitHub tokens and scopes, the GraphQL and REST APIs, rate limits, GitHub Actions, uv, SQLite,
IANA time zones, ISO weeks, percentiles, DORA, `jq`, `curl` and loopback addresses.

The README shrinks to the pitch, the install steps, a first report and a link to the guide, plus its
contributor sections (Updating the shared rules). The reference tables move to the guide, which
becomes their only copy (decided 2026-11-01).

## Module location

- `mkdocs.yml`: the site configuration.
- `docs/`: the pages, `docs/assets/` (theme CSS, logo, favicon), `docs/images/` (screenshots) and
  `docs/snippets/` (included fragments).
- `bin/screenshots.py`, `bin/screenshots.sh`: they capture the screenshots.
- `src/tests/test_docs.py`: the drift test.
- `.github/workflows/docs.yml`: builds and deploys the site.

## Pages

The nav, in order. Each entry lists the page's diagrams (D) and screenshots (S).

| Page | Content |
|------|---------|
| `index.md` Home | The pitch, one command and the HTML report it makes (S: HTML report tiles and charts, light), where to start, why wambatic, its limits in one line each |
| `install.md` Installation | Python 3.14 and [uv](https://docs.astral.sh/uv/) with links to their installers; clone, `uv sync`, `source bin/activate.sh`; checking the install; shell completion with `--completion generate`; updating with `git pull` and `uv sync` |
| `token.md` The GitHub token | What a personal access token is ([GitHub docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)); classic scopes (`public_repo`, `repo`, `read:org`) against fine-grained permissions; `gh auth token` as the fallback; that the token is never stored or printed; when no token is needed. D: flowchart of how the token is found |
| `getting-started.md` Getting started | A first report on `repo:pallets/click`, read section by section (S: terminal report, split into sections); a second run from the warm cache; the same data as HTML and JSON |
| `concepts.md` How wambatic works | D: architecture flowchart (GitHub GraphQL and REST, then fetch, the SQLite cache, stats, then terminal, HTML, JSON and web); D: sequence diagram of an incremental sync (listing, watermark minus `fetch.overlap`, conditional requests with [ETags](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#use-conditional-requests-if-appropriate)); the [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) and `fetch.on_rate_limit` |
| `guide/targets.md` Targets | `user:`, `org:`, `repo:` and bare names; what a user target counts; forks and archived repositories. D: flowchart from a target to the repositories that are read |
| `guide/periods.md` Periods and ranges | `--by`, `--since`, `--until`, `--tz`; partial periods and the `*`; [ISO weeks](https://en.wikipedia.org/wiki/ISO_week_date) starting on Monday. D: timeline (Mermaid `gantt`) showing a range cut into months, with the partial first and last months |
| `guide/terminal.md` The terminal report | Every section in output order, each with its own screenshot (S: every section of `repo:pallets/click` and `org:pallets --by-author`); sparklines; no meaning carried by colour alone |
| `guide/html.md` The HTML report | Where the file goes and how it is named; the period switch; themes; offline and shareable. S: full page light, full page dark, the period switch, the commit calendar, one chart with a partial period |
| `guide/web.md` The web app | Starting, the form, the progress page, freshness, the JSON routes, `/docs`, security, stopping. S: form, progress page, report page, `/docs`. D: state diagram of a sync job (waiting, listing, syncing, done, failed); D: sequence diagram of `/api/stats` answering 202, `/api/progress`, then `/api/stats?job=`; D: flowchart of the `Host` check and why loopback ([DNS rebinding](https://en.wikipedia.org/wiki/DNS_rebinding)) |
| `guide/json.md` JSON output | The shape (`format_version`, `subject`, `request`, `series`, the tables, provenance) as an annotated example; `jq` recipes ([jq manual](https://jqlang.org/manual/)). D: class diagram of the document's objects |
| `guide/activity.md` Activity | Commits, contributors, active days, lines; merge commits; bots |
| `guide/flow.md` Flow | Pull requests and issues; review, merge and close times; [percentiles](https://en.wikipedia.org/wiki/Percentile). D: timeline of one pull request (opened, first review, merged) and the periods its events land in |
| `guide/delivery.md` Delivery and DORA | Runs, releases and the [DORA](https://dora.dev/guides/dora-metrics-four-keys/) proxies; `stats.deploy_workflow`, `stats.hotfix_labels`, `stats.failure_window`. S: the delivery charts of the HTML report. D: flowchart of what counts as a deployment; D: timeline of lead time and of a failed change |
| `guide/popularity.md` Popularity | Stars, forks, watchers, languages; the cost of the first sync. S: the popularity charts and the languages chart |
| `guide/cache.md` The cache | Where it is, `cache info` (S: terminal), `cache clear`, the version check and `--ignore-cache-version`, full refreshes. D: flowchart of the sync-or-not decision (`--no-fetch`, `--max-age`, `--full-refresh`, `fetch.full_refresh_after`) |
| `guide/config.md` Configuration | Layers, the file, `WAMBATIC_CONFIG`, durations, an annotated example. D: flowchart of the layers |
| `guide/recipes.md` Recipes | The README's common workflows, plus a nightly HTML report with `cron`, and an offline report on a laptop |
| `guide/troubleshooting.md` Troubleshooting | Each one-line error message and what to do about it; rate limits; a slow first sync |
| `reference/cli.md` Command line | One options table for each of the global options, `report`, `serve` and `cache` |
| `reference/settings.md` Settings | Every setting: key, type, default, meaning and trade-off |
| `reference/metrics.md` Metrics | Every metric: name, group, unit, definition, linked to its guide page |
| `reference/exit-statuses.md` Exit statuses | The README's table |
| `limits.md` Limits | The README's list, each with why |

Each guide page opens with one sentence saying what it is for, gives a working command before the
options, and ends with links to the related pages. Every external term links, the first time it
appears on a page, to its primary documentation (GitHub, MkDocs, uv, IANA, DORA and so on), not to
blog posts. British English throughout.

## Screenshots

`bin/screenshots.sh` runs `bin/screenshots.py`, which writes every image under `docs/images/` and is
run by hand when the output changes. It needs `GITHUB_TOKEN` (or `gh auth token`) and Playwright's
Chromium.

- **Data.** Real public data: `repo:pallets/click` for single-repository views, `org:pallets` for the
  by-repository, by-author and progress views (decided 2026-11-01). The range is fixed in the script:
  `--since 2024-11-01 --until 2026-10-31` for `--by month`, so a re-run on later days shows the same
  periods. Groups are `activity,flow,delivery,popularity`.
- **Cache.** A dedicated cache, `~/.cache/wambatic/docs.sqlite3`, set through a temporary
  `WAMBATIC_CONFIG`. The user's own cache is never touched. A re-run syncs only what is new.
- **Terminal.** It calls `wambatic.reports.terminal.render_terminal` with a
  `rich.console.Console(record=True, width=110, force_terminal=True)` and exports each section as SVG
  with `export_svg`. Sections are cut at the `heading` lines, and the whole report is also kept as
  one SVG. Captures include `cache info`.
- **HTML report.** Playwright opens the file written by `report --format html` at a 1280 by 800
  viewport. It takes full pages with `prefers-color-scheme` light and dark, and crops of single
  elements by CSS selector (tiles, the switch, the calendar, named charts). The selectors live in one
  table at the top of the script.
- **Web app.** It starts `wambatic serve` on a free loopback port with `--max-age 30d` and captures
  the form, the report page and `/docs`. The progress page comes from `org:pallets` against a
  second, empty throwaway cache, captured once the state reads "Syncing repositories". Then the
  server is stopped.
- **Format.** Terminal output as SVG, browser pages as PNG. Each PNG goes through Playwright's
  `scale: 'css'`, to keep files small; a file over 1 MB fails the run.
- **Date.** The script writes `docs/snippets/captured.md`, one line naming the capture date, the
  wambatic version and the subjects. Every page with a screenshot includes it as a dated note
  ([pymdownx.snippets](https://facelessuser.github.io/pymdown-extensions/extensions/snippets/)).
  Screenshots are dated records and are never edited by hand.

## API

```python
# bin/screenshots.py
def capture_terminal(result: wambatic.stats.base.StatsResult, out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Render `result` as the terminal report and write one SVG per section plus the whole report."""

def capture_html(report_path: pathlib.Path, out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Screenshot the HTML report, light and dark, and the element crops named in SELECTORS."""

def capture_web(config_path: pathlib.Path, out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Start `wambatic serve`, screenshot its pages, stop it."""

def main() -> int:
    """Sync the docs cache, capture everything, write docs/snippets/captured.md; return the exit status."""
```

```python
# src/tests/test_docs.py
def doc_table(page: pathlib.Path, heading: str) -> list[dict[str, str]]:
    """The rows of the first Markdown table under `heading` in `page`, keyed by column header."""

def test_cli_options_match(): ...       # reference/cli.md against the cappa command dataclasses
def test_settings_match(): ...          # reference/settings.md keys and defaults against wambatic.settings
def test_metrics_match(): ...           # reference/metrics.md against TOTAL_METRICS, FLOW_METRICS,
                                        # DELIVERY_METRICS and POPULARITY_METRICS, with units
def test_groups_match(): ...            # the groups named in the guide against wambatic.stats.base.GROUPS
def test_images_exist(): ...            # every image a page references exists, every image is referenced
```

## Drift test

`src/tests/test_docs.py` reads the Markdown and fails on any difference, in both directions: a row
the code lacks, or code the page lacks.

- **CLI.** It checks the option names of the `Wambatic`, `Report`, `Serve` and `CacheCommand`
  dataclasses in `wambatic.cli` (the field name in kebab case with `--`, plus short forms). Positional
  arguments are the upper-case field name.
- **Settings.** It checks every field of `FetchSettings`, `StatsSettings` and `ReportSettings` as
  `section.field`. A documented default is parsed back (durations with
  `wambatic.settings.parse_duration`, lists and booleans as JSON, paths with `expanduser`, `none` as
  `None`) and compared with the dataclass default.
- **Metrics.** It checks each metric's name and unit.
- **Images.** It checks that every image path a page references exists, and that every file under
  `docs/images/` is referenced.

The test does not mirror a source module, so `AGENTS.md`'s list of test-layout exceptions gains it.
A strict MkDocs build (below) catches broken internal links and nav entries.

## Implementation

- **`mkdocs.yml`.** Material, with the features `navigation.sections`, `navigation.top` and
  `content.code.copy`, and `content.code.annotate` for the JSON page. It uses metafopy's fonts (Mona
  Sans, Source Code Pro) and the extensions `admonition`, `attr_list`, `md_in_html`, `tables`,
  `toc` (permalink), `pymdownx.highlight`, `pymdownx.snippets` and `pymdownx.superfences`, with a
  `mermaid` custom fence ([Material diagrams](https://squidfunk.github.io/mkdocs-material/reference/diagrams/)).
  Its plugins are `search` only. There is no API reference: wambatic is a command, not a library.
- **Theme.** `docs/assets/theme.css` copies metafopy's colour variables, header rule and search box,
  without the metafopy-only rules. Material styles the Mermaid diagrams to match.
- **Logo.** `docs/assets/wambatic-mark.svg` and `favicon.svg`: a hairline white box (graphite
  `#3D3F44` rule) holding a strip of three rows of seven small squares that darken left to right,
  after the report's commits-by-day heatmap and in its light sequential ramp (`figures.py`), with
  `#E8F1FC` for an empty cell. The favicon is the same idea in a 3 by 3 grid, legible at 16 px. No
  animation.
- **Light and dark.** Material's palette toggle, with both schemes, so that the dark screenshots have
  a matching site.
- **Dependencies.** A `docs` dependency group in `pyproject.toml` (`uv add --group docs mkdocs
  mkdocs-material`), so the lockfile pins the versions. `uv sync` leaves it out; `uv sync --group
  docs` installs it.
- **CI.** `.github/workflows/docs.yml`, as metafopy's. It runs on pull requests, on pushes to main
  touching `docs/**`, `mkdocs.yml` or the workflow, and on manual dispatch. It installs with `uv sync
  --group docs` and runs `mkdocs build --strict` on PRs, or `mkdocs gh-deploy --strict --force
  --no-history` on main. The action versions are those of `.github/workflows/ci.yml`. The
  repository's Pages source must be set to the `gh-pages` branch once, by hand.
- **README.** It is cut as described in the introduction, and its "More" section links the guide.
  `pyproject.toml` gains `[project.urls] Documentation`.
- **AGENTS.md.** Layout gains `docs`. Checks gains the docs workflow and `test_docs.py`. A line says
  that a change to user-visible behaviour updates the guide in the same commit.

## Error handling

- `bin/screenshots.py` exits 1 with one line on stderr in each of these cases, and leaves the
  images it has not reached unchanged:
  - no token;
  - no Chromium (`playwright install chromium`);
  - a sync error (the wambatic error's own message);
  - a selector that matches nothing (names the selector);
  - a server that does not answer within 30 s;
  - an image over 1 MB.
- `test_docs.py` fails with each mismatch named: the page, the row, the expected and actual value.
- The docs workflow fails on any `mkdocs build --strict` warning: a broken link, a missing nav file,
  or a missing snippet.

## External dependencies

- `mkdocs` 1.6.1 (released 2024-08-30, quiet but not archived) and `mkdocs-material` 9.8.0
  (2026-10-24, active). Both were checked on PyPI on 2026-11-01. If Material stops supporting
  MkDocs, its successor [Zensical](https://zensical.org/) reads `mkdocs.yml`.
- Mermaid is loaded by Material at page view from a CDN; the built site needs the network to draw
  the diagrams.
- `playwright` (already a dev dependency) and `rich` (runtime) for the screenshots.
- GitHub Pages and the real GitHub API (for the screenshots only).
- The `docs` dependency group declares packages that are run as commands, never imported. The audit
  check D2 flags such packages until the open request in the agents repository's auditme
  `requests.md`, "D2 should not flag dependencies that are only run as commands", is shipped. Check
  for it in `.agents/claude/skills/auditme/requests.md` before the last task. If it is still open,
  accept the hits with markers, as was done for the dev tools.
