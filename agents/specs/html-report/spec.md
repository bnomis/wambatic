# HTML report

**Version:** 2.1
**Status:** implemented
**Date:** 2026-11-11

The static HTML report of `--format html`, also served by the web app: its figures, page layout, tabs, tables, granularity switch, palette and themes, table export, and the headless-browser test. Part of [Reports](../reports/spec.md).

Version 1.0 is the reports spec 1.12 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [reports reviews](../reports/review-1.md) in `agents/specs/reports/`.

Version 1.1 shows the GitHub host in the provenance footer as the terminal does ([Fetch](../fetch/spec.md) 1.16, [fetch review 1](../fetch/review-1.md)).

Version 1.2 shows the branch and excluded-files lines in the provenance footer as the terminal does ([Commit sync](../commit-sync/spec.md); [commit sync review 1](../commit-sync/review-1.md)).

Version 1.3 names both zones in the header as the terminal does ([Author timezones](../author-timezones/spec.md); [author timezones review 1](../author-timezones/review-1.md)).

Version 2.0 (asked for on 2026-11-11, because the page had grown too long to read) puts the summary tiles first and each section in a tab, puts every table in a collapsible block that starts closed when the table is long, makes table columns sortable and filterable, and adds CSV and Excel export of each table. The page is no longer one self-contained file: the user decided on 2026-11-11 that it only has to open in a browser, so its scripts and stylesheet move to an assets folder written beside it, which still opens offline from disk. The choices were made in this session's interview: the tab split, the folder over a CDN, and `write-excel-file` for Excel. The [GraphQL API](../graphql-api/spec.md) replacing the REST routes is a separate spec.

Version 2.1 (2026-11-12) reuses an existing assets folder only when its files match this version's byte for byte, and otherwise refuses to write, so a folder planted in a shared directory cannot put its scripts in the page.

## Module location

`src/wambatic/reports/figures.py`, `src/wambatic/reports/html.py`, its `templates/` (`report.html`, `report.css`, `report.js`, and since 2.0 `tables.js`), and since 2.0 `src/wambatic/reports/assets.py` with the vendored `src/wambatic/reports/vendor/write-excel-file.min.js` and its `LICENSE`. Its tables come from `rows.py` ([Terminal report](../terminal-report/spec.md)). Tests are in `src/tests/reports/`, the headless-browser test in `src/tests/reports/test_html_browser.py`.

## API

```python
import dataclasses
import pathlib
import typing

@dataclasses.dataclass(frozen=True, slots=True)
class Figure:
    key: str                          # unique in the page and the chart element's id: 'activity-commits'
    group: typing.Literal['activity', 'delivery', 'flow', 'popularity']
    title: str                        # shown above the chart: 'Commits per period'
    description: str                  # one sentence, the chart's aria-label
    data: list[dict[str, object]]     # Plotly traces as plotly.js JSON; colours left to the theme
    layout: dict[str, object]         # Plotly layout as plotly.js JSON; colours left to the theme

def build_figures(result: StatsResult) -> list[Figure]:
    """The per-period charts of the result's total series, in page order; [] for a TOTAL result."""
def build_range_figures(total: StatsResult) -> list[Figure]:
    """The whole-range charts of a TOTAL result: top contributors, by repository, by author, languages."""
def build_calendar(day: StatsResult) -> Figure | None:
    """The daily-commits heat-map of a DAY result; None without activity series.
    Raises UsageError for any other granularity."""

@dataclasses.dataclass(frozen=True, slots=True)
class HtmlReport:
    total: StatsResult                       # Granularity.TOTAL: tiles, whole-range charts and tables
    periods: dict[Granularity, StatsResult]  # exactly YEAR, MONTH, WEEK and DAY
    initial: Granularity                     # the granularity shown on load; a key of `periods`

def html_document(
    report: HtmlReport, theme: typing.Literal['auto', 'dark', 'light'], assets_url: str
) -> str:
    """The whole page; pure. Its script and stylesheet elements point at `assets_url` (a URL path
    ending in '/': the relative `wambatic-assets-HASH/` for a file, `/assets/HASH/` in the web
    app). Raises UsageError when the five results differ in anything but granularity (subject,
    groups, since, until as requested, by_author, tz, settings)."""
def report_filename(subject: Subject) -> str:
    """'repo-OWNER-NAME.html', 'user-NAME.html' or 'org-NAME.html'."""
def render_html(
    report: HtmlReport, out: pathlib.Path, theme: typing.Literal['auto', 'dark', 'light']
) -> pathlib.Path:
    """Write the assets folder beside `out` with `write_assets(out.parent)`, then
    `html_document(report, theme, folder_name + '/')` to `out` atomically; return `out`."""

# assets.py (2.0)
@dataclasses.dataclass(frozen=True, slots=True)
class Asset:
    name: str            # file name in the folder: 'plotly.min.js', 'report.js', 'tables.js',
                         # 'write-excel-file.min.js', 'report.css'
    content: bytes
    media_type: str      # 'text/javascript; charset=utf-8' or 'text/css; charset=utf-8'

def page_assets() -> tuple[Asset, ...]:
    """Every file the page loads, in a fixed order; built once per process and cached."""
def assets_hash() -> str:
    """The first 12 hex digits of the SHA-256 of every asset's name and content, in order."""
def assets_folder_name() -> str:
    """'wambatic-assets-' + assets_hash()."""
def write_assets(directory: pathlib.Path) -> pathlib.Path:
    """Write `assets_folder_name()` under `directory` unless it already exists; return its path.
    The folder is written as a temporary sibling and renamed into place, so it is complete or
    absent. An existing folder is kept only when it is a real directory whose files match
    `page_assets()` byte for byte. Raises OutputError (`cannot write PATH: REASON`) when it
    cannot be written, or when it exists and does not hold this version's files."""

def period_requests(request: StatsRequest) -> list[StatsRequest]:
    """The five requests of an HTML report: `request` with granularity TOTAL, then YEAR, MONTH,
    WEEK and DAY, everything else unchanged (in `html.py`)."""
@dataclasses.dataclass(frozen=True, slots=True)
class PageFigures:
    """Every figure of one page, each built once by `build_page_figures`: the per-period figures of
    each granularity, the range figures and the calendar."""
    periods: dict[Granularity, list[Figure]]
    range_figures: list[Figure]
    calendar: Figure | None
def build_page_figures(report: HtmlReport) -> PageFigures: ...
def html_report(results: list[StatsResult], initial: Granularity) -> HtmlReport:
    """The `HtmlReport` of the five results of `period_requests`, in that order (in `html.py`)."""
```

## Error handling

- `--out` (step 7), and the default HTML path, are written to a temporary file in the target's directory and moved into place with `os.replace`, so no partial file is left behind; the temporary file is removed when the write fails.
- Since 2.0 the assets folder is written first, as a temporary sibling directory renamed into place; when the rename fails because another run made the same folder meanwhile, the existing folder is kept and the temporary one removed. Since 2.1 an existing folder, found before the write or after a lost rename, is kept only when it is a real directory (not a symlink) whose files match `page_assets()` byte for byte; otherwise the run fails with `OutputError` `cannot write PATH: it exists and does not hold this version's files; remove it` (exit 1) and the page is not written. The page is rewritten on every run but the folder is reused, so without this check a folder planted in a shared directory such as `/tmp` would put its scripts in every page written there (found by a security review on 2026-11-12). A failure to write it is the same `OutputError` (exit 1) as a failure to write the page, and the page is then not written, so no page ever points at a missing folder.
- A page copied without its folder says so: right after the header it holds `<p class="assets-missing">`, `This report's files (wambatic-assets-HASH) did not load; keep the page beside that folder.`, which only `report.css` from the folder hides. A script that did not load can show nothing, so the notice is shown by default and hidden by the stylesheet. Without the folder the tiles, tables and footer still show, unstyled, and every tab panel shows in order, as without script.
- The folder name carries the hash of its contents, so a page always loads the files it was made with: a newer wambatic writing into the same directory adds a folder beside the old one and never changes it.
- An export that fails in the browser (the Excel library missing, a download blocked) shows one line beside the table's buttons and writes nothing; it never throws to the console.

## Implementation

**Static HTML.** One page built by `html_document` from an `HtmlReport`, beside one assets folder (review-2.md has the reasons for the choices of 1.x below; 2.0's are in its version line).

- *Offline, with an assets folder* (2.0; until 1.3 everything was inlined in one file). The page loads, by relative URL under `assets_url`, the files of `page_assets()`: `plotly.min.js` (from `plotly.offline.get_plotlyjs()`; MathJax is not included), `write-excel-file.min.js` (vendored), `tables.js`, `report.js` and `report.css` (the palette tokens filled in as before). The scripts are plain `<script defer src=...>`, not modules, because Chromium and Firefox refuse module scripts from `file://` URLs. The page's own data stays inline (below). No URL points outside the page and its folder, and no web font is used (system sans: `system-ui, -apple-system, "Segoe UI", sans-serif`), so the page opens from disk with no network; it can be hosted together with its folder, for instance on GitHub Pages. The templates are read with `importlib.resources` and filled with stdlib `string.Template`; no templating library is added.
- *Escaping.* Every text from the data (logins, repository names, labels) reaches the page through `html.escape`. The figures and the client script's data are one JSON object in `<script type="application/json" id="wambatic-data">`, written with `json.dumps(..., ensure_ascii=False)` and then `<`, `>` and `&` replaced by `\u003c`, `\u003e` and `\u0026`, so no data can close the script element.
- *Layout*, in this order; a section appears only when the result has its group's series, as in the terminal:
  1. A header: `wambatic` and the subject (`repo octocat/Hello-World`), the range of the `TOTAL` result, the timezone (since 1.3 the terminal's `commits in authors' zones, other events in <timezone>` when `provenance['commit_timezone']` is `'author'`), and the granularity switch: a radio group Year, Month, Week, Day with `initial` checked.
  2. Summary tiles from the `TOTAL` result: Commits, Contributors (top-contributors rows other than `unattributed`), Lines added, Lines deleted and Net lines (signed) for `activity`; PRs opened, PRs merged, Issues opened, Issues closed and Median time to merge (hours, one decimal place; `-` with no value) for `flow`; Workflow runs, Success rate, Releases, and Deployments and Median lead time when those proxies are emitted, for `delivery`; Stars, Forks and Watchers (the sums of `tables['popularity']`) and Top language (the first row of `tables['languages']` other than `Other`, `-` when there is none) for `popularity`. Numbers are formatted as in the terminal.
  3. Since 2.0, the tab bar and one tab panel per section, in this order; a tab and its panel appear only when the panel has content. The `activity` group fills three tabs:
     - *Commits*: Commits per period and Active days per period, the Commits by day calendar from the `DAY` result (not switched), and the Activity by period table (one per granularity, all but the shown one `hidden`).
     - *Contributors*: Contributors per period, then the Top contributors chart and table (every row; the chart shows the first `TOP_CONTRIBUTORS_SHOWN`), the By author chart and table, and the By repository chart and table.
     - *Lines*: Lines added and deleted per period.
     - *Flow*: the per-period charts of `build_figures` for `flow`, then Flow by period and Flow times by period, one table per granularity as above.
     - *Delivery*: the per-period charts of `build_figures` for `delivery`, then Delivery by period and, when a proxy is emitted, DORA proxies by period, one table per granularity as above, with a line under the tab's heading that the DORA figures are proxies and how each is measured is in the README.
     - *Popularity*: the per-period charts of `build_figures` for `popularity`, the Languages chart of `build_range_figures`, then Popularity by period (one table per granularity, as above), Popularity now and Languages (every row; the chart shows at most `TOP_LANGUAGES_SHOWN` bars, the last an `Other` bar summing the rest when there are more), with a line under the tab's heading that the counts are as of the last sync and the totals count the stars and forks that exist now.
  4. Unavailable, when `tables['unavailable']` is not empty, below the panels and outside every tab, so it is never hidden.
  5. A provenance footer: the terminal's items (with its GitHub host line, 1.1, and its branch and excluded-files lines, 1.2), the plotly.js version (`plotly.offline.get_plotlyjs_version()`), the version of `write-excel-file` (2.0), and the `--ignore-cache-version` warning when `version_override_at` is present.
  Tables hold the same rows and columns as the terminal's, from `rows.py`, so the two never disagree; they are the page's data view and work without script.
- *Tabs* (2.0). The tab bar is a `role="tablist"` of buttons, each `role="tab"` with `aria-controls` naming its panel, a `<section role="tabpanel">` with an `id` of `tab-commits`, `tab-contributors`, `tab-lines`, `tab-flow`, `tab-delivery` or `tab-popularity`. One panel shows at a time; the others carry `hidden`. The first present tab shows on load, unless the URL's fragment names a present panel (`#tab-flow`), which then shows; choosing a tab sets the fragment with `history.replaceState`, so a link opens on that tab and the back button does not step through tabs. Left and right arrow keys move between tabs, Home and End go to the first and last, as the WAI-ARIA tabs pattern asks. Without script the tab bar is hidden and every panel shows, one after another, each under its heading, so the page reads as in 1.3. A chart is drawn with `Plotly.newPlot` the first time its panel shows, since Plotly sizes a chart in a hidden panel to zero width; a granularity change redraws the charts of the shown panel at once and marks the others to be redrawn with the new granularity when they next show.
- *Built once.* `html_document` builds each period's `build_figures`, the `build_range_figures` of the `TOTAL` result and the `build_calendar` of the `DAY` result once, and every part of the page (the chart elements, the sections, the embedded data) reads those; it never calls a builder a second time for the same result. A section's presence test reuses the table it then renders rather than building it to test for `None`. In `rows.py`, `figures.py` and `terminal.py` a function that needs a result's total series and bucket list derives each once and passes them on. The output is unchanged byte for byte: the existing HTML, terminal and JSON tests are the check.
- *Granularity switch.* All four period results are embedded as figures and pre-rendered tables. Choosing a granularity calls `Plotly.react` on each per-period chart with that granularity's figure and toggles the `hidden` attribute of the period tables; nothing is recomputed in the browser. Only total series are embedded per period (never the per-repo or per-author breakdowns, which would grow with repos times days); the breakdown charts and tables come from the `TOTAL` result.
- *Charts* (`build_figures`, per period, in this order): Commits, Contributors and Active days per period (bars, one each), Lines added and deleted per period (added as bars above zero and deleted as negative bars below it with `barmode='relative'`, net as a line on the same axis); Pull requests per period (grouped bars, opened and merged), Issues per period (grouped bars, opened and closed), Time to first review, Time to merge and Time to close (each a p50 and a p90 line, hours, a gap where a bucket has no value), PR size (p50 line, lines); Workflow runs per period (bars), Workflow success rate (line, 0 to 100 per cent on a fixed axis), Workflow duration (p50 and p90 lines, minutes), Releases per period (bars), Release interval (p50 line, days), then, each only when its series is present, Deployments per period (bars), Lead time (p50 and p90 lines, hours), Change failure rate (line, per cent on a fixed 0 to 100 axis) and Time to restore (p50 and p90 lines, hours); Stars per period (bars, `stars_added`), Stars over time (line, `stars_total`), Forks per period (bars, `forks_added`) and Forks over time (line, `forks_total`). Ratios are shown as percentages, the series' 0 to 1 values multiplied by 100. `build_range_figures`: Top contributors (horizontal bars of commits, first `TOP_CONTRIBUTORS_SHOWN`, largest at the top), By repository and By author (horizontal bars of commits, each when that breakdown is present, all-zero rows left out as in the terminal), and Languages (horizontal bars of each language's share in per cent, the rows of `tables['languages']` in its order, cut to `TOP_LANGUAGES_SHOWN` bars with one `Other` bar summing the rest when there are more, first row at the top; group `popularity`, present when the table is not empty). `build_calendar`: a heat-map of commits by day, one column per ISO week (x is the week's Monday) and one row per weekday, Monday at the top. Every chart has one y-axis; there are no dual axes.
- *Partial buckets.* Bars of a bucket in `provenance['partial_buckets']` carry a diagonal hatch (`marker.pattern.shape` `'/'`); line points in such a bucket have open markers; a chart with a partial bucket has the caption `hatched or open: partial period`.
- *Palette and themes.* Colours follow the validated reference palette of the dataviz skill (read 2026-10-30), held as `PALETTE` in `figures.py`: categorical slots 1 to 3, light `#2a78d6`, `#eb6834`, `#1baf7a`, dark `#3987e5`, `#d95926`, `#199e70` (no chart has more than three series, the most the palette validates for every pair); the heat-map's sequential blue ramp `#cde2fb`, `#86b6ef`, `#3987e5`, `#256abf`, `#0d366b` on light and `#104281`, `#1c5cab`, `#3987e5`, `#6da7ec`, `#b7d3f6` on dark (low to high, so more commits are brighter on the dark surface); chart surface `#fcfcfb` / `#1a1a19`, page `#f9f9f7` / `#0d0d0d`, primary ink `#0b0b0b` / `#f0efec`, secondary ink `#52514e` / `#c3c2b7`, gridlines `#e1e0d9` / `#2c2c2a`. Figures carry no colours: each trace has `meta: {"slot": n}` and the client script fills trace colours and layout colours from the active theme before each `Plotly.react`. `report.html_theme` `light` or `dark` sets `data-theme` on `<html>`; `auto` follows `prefers-color-scheme` and re-themes the charts when it changes. Text never wears a series colour.
- *Labels and hover.* A chart with one series has no legend (its title names it); with two or three it has a legend and each line is labelled at its last point. Hover shows each point's value (`hovermode='x unified'` on per-period charts). Each chart's element has `role="img"` and its `description` as `aria-label`.
- *Testing.* Unit tests validate every figure with `plotly.graph_objects.Figure(data=..., layout=...)`, which rejects an unknown property. Since 2.0 unit tests also check that `assets_hash` changes when any asset's content changes, that `write_assets` leaves an existing folder holding the same files untouched, refuses one with an edited file or that is a symlink, and a failed write leaves no folder, that every numeric cell's `data-value` equals the value its text was formatted from, and that the vendored library's SHA-256 matches the one recorded in `assets.py` beside its version. A headless-browser test (`src/tests/reports/test_html_browser.py`, marker `browser`) opens the page from disk with [Playwright for Python](https://playwright.dev/python/) and Chromium, aborts and records every request that is not the page or a file in its assets folder, and checks there is none, no console error and no page error, that every chart in every tab rendered with a non-zero width once its tab showed, that each of the four granularities shows its own number of buckets, including in a tab first opened after the switch, that dark and light themes apply, that the arrow keys and the URL fragment choose tabs, that a long table starts closed and a short one open, that sorting a numeric column orders by value and a third click restores the original order, that each filter form narrows the rows and updates the count, and that the CSV and Excel buttons download files (Playwright's download event) whose rows match the shown rows; the Excel file is read back with `openpyxl` in the test (a development dependency). A page opened without its folder shows the missing-files notice and every panel. It launches Playwright's own Chromium, else the cloud environment's preinstalled `/opt/pw-browsers/chromium`, else skips with that reason; CI's `browser` job installs Chromium with `playwright install --with-deps chromium` and runs it.

## Tables

Since 2.0 every data table (every table of the Layout above except Unavailable, which stays a plain table so it is never hidden) gets the same four things from `tables.js`. The table's HTML is written by `html.py` and stays complete without script; the script only adds controls.

- *Collapsible.* Each table, or for the period tables the four tables of one kind (one per granularity), is wrapped in a `<details class="table-block">` whose `<summary>` is the table's title and its row count (`Top contributors (412 rows)`, the count of the shown granularity's table, updated on a switch). It starts open when the table has at most `TABLE_OPEN_ROWS` (10) rows of body, else closed; for the period tables the test is on the `initial` granularity's table. `<details>` works without script. The `<caption>` stays in the table for screen readers.
- *Values.* `html.py` writes each header cell with `data-type="number"` or `data-type="text"` (the first column, and every column of a text kind such as Login, Name, Language, Repository, Metric and Reason, are text), and each numeric body cell with `data-value`, the number the cell's text was formatted from, written with `repr` of a float or `str` of an int, or empty when the value is `None` (the `-` cells). The period tables already hold their raw values in `PeriodTable.rows`; the other table builders pass the raw values they format. Sorting, filtering and export read `data-value`, never the formatted text, so `1,234`, `+56` and `12.5%` sort and export as numbers. Ratios keep the 0 to 100 percentage they show, so a sheet holds what the page shows.
- *Sortable.* Each header cell gets a button. A click sorts the body ascending, a second descending, a third back to the order `html.py` wrote; the header's `aria-sort` follows (`ascending`, `descending`, `none`) and a small arrow shows the direction. Numbers compare by value and empty values sort last both ways; text compares with `Intl.Collator(undefined, {numeric: true, sensitivity: 'base'})`. The sort is stable, the `<tfoot>` total row never moves, and each table of a period group keeps its own sort.
- *Filterable.* A row of inputs under the header, one per column, inserted by the script (so none shows without script). A text column keeps rows whose text contains the input, ignoring case. A number column takes `N`, `=N`, `>N`, `>=N`, `<N`, `<=N` or `A..B` (inclusive), where a number may carry `,` separators and a `%`; an input that matches none of these forms is marked `aria-invalid="true"` and filters nothing. Filters on several columns combine with AND; a row with an empty value fails every number filter but an empty one. Filtering hides rows with `hidden`, is applied 150 ms after the last keystroke, and updates a `role="status"` line `Showing 37 of 412 rows`. The summary's count stays the full count. The total row is not recomputed and is marked `Total (all rows)` while a filter is active, so it is never mistaken for a total of the shown rows.
- *Export.* Beside each table, two buttons, `CSV` and `Excel`, export the rows currently shown, in their shown order, with the header row and without the total row. A file is named after the page and the table: `repo-pallets-click-top-contributors.csv` (the page's file stem from `report_filename`, then the table title slugified: lower case, runs of other characters to one `-`), with the granularity added for a period table (`...-activity-by-period-month.xlsx`). CSV is RFC 4180 (comma, CRLF, a field quoted when it holds a comma, quote or line break, quotes doubled), UTF-8 with a byte order mark so Excel reads non-ASCII logins, numbers written from `data-value` without separators, and empty values as empty fields. A text cell that starts with `=`, `+`, `-` or `@` is written with a leading `'` so a spreadsheet does not run it as a formula, since logins and repository names come from GitHub. Excel uses `writeXlsxFile` from the vendored `write-excel-file`, one sheet named after the table (cut to Excel's 31 characters, without `[]:*?/\`), the header row bold, numbers as numbers and text as text, so no formula is ever written. Both downloads go through a `Blob` URL and an `<a download>` click, which works for a page opened from disk, and the URL is revoked afterwards.

**Visualisation choices.** Line charts for trends, bars for per-bucket counts, stacked bars for added and deleted lines with net as an overlaid line, heat-map calendar for daily commit activity, horizontal bars for contributors and languages. Partial first and last buckets are hatched. The Static HTML paragraph above settles each (step 7, languages in step 10).

## External dependencies

- [Plotly](https://plotly.com/python/) for Python, whose bundled plotly.js (`plotly.offline.get_plotlyjs()`) becomes `plotly.min.js` in the assets folder; as in 1.x.
- [write-excel-file](https://gitlab.com/catamphetamine/write-excel-file) 4.1.1 (MIT, released 2026-06-08, read on npm 2026-11-11), chosen by the user on 2026-11-11 over SheetJS (current versions only on its own CDN) and exceljs (last release 2023-10-19). Its browser bundle `bundle/write-excel-file.min.js` (about 70 KB) is vendored at `src/wambatic/reports/vendor/write-excel-file.min.js` with its `LICENSE`; `assets.py` records the version and the SHA-256 of the file, and a test fails when the file and the record disagree. An upgrade is a deliberate change: replace the file, update both records, and the folder hash changes with it. The bundle defines the global `writeXlsxFile`.
- Development only: [openpyxl](https://openpyxl.readthedocs.io/) (MIT; 3.1.5, released 2024-06-28, quiet but feature-complete), for the browser test to read an exported `.xlsx` back.
- No other library: the tabs, sorting, filtering and CSV writer are written in `tables.js` and `report.js`, which stay small enough to read.
