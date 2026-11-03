# HTML report

**Version:** 1.3
**Status:** proposed
**Date:** 2026-11-03

The self-contained static HTML report of `--format html`, also served by the web app: its figures, page layout, granularity switch, palette and themes, and the headless-browser test. Part of [Reports](../reports/spec.md).

Version 1.0 is the reports spec 1.12 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [reports reviews](../reports/review-1.md) in `agents/specs/reports/`.

Version 1.1 shows the GitHub host in the provenance footer as the terminal does ([Fetch](../fetch/spec.md) 1.16, [fetch review 1](../fetch/review-1.md)).

Version 1.2 shows the branch and excluded-files lines in the provenance footer as the terminal does ([Commit sync](../commit-sync/spec.md); [commit sync review 1](../commit-sync/review-1.md)).

Version 1.3 names both zones in the header as the terminal does ([Author timezones](../author-timezones/spec.md); [author timezones review 1](../author-timezones/review-1.md)).

## Module location

`src/wambatic/reports/figures.py`, `src/wambatic/reports/html.py` and its `templates/` (`report.html`, `report.css`, `report.js`); its tables come from `rows.py` ([Terminal report](../terminal-report/spec.md)). Tests are in `src/tests/reports/`, the headless-browser test in `src/tests/reports/test_html_browser.py`.

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

def html_document(report: HtmlReport, theme: typing.Literal['auto', 'dark', 'light']) -> str:
    """The whole self-contained page; pure. Raises UsageError when the five results differ in
    anything but granularity (subject, groups, since, until as requested, by_author, tz, settings)."""
def report_filename(subject: Subject) -> str:
    """'repo-OWNER-NAME.html', 'user-NAME.html' or 'org-NAME.html'."""
def render_html(
    report: HtmlReport, out: pathlib.Path, theme: typing.Literal['auto', 'dark', 'light']
) -> pathlib.Path:
    """Write `html_document(report, theme)` to `out` atomically and return `out`."""

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

## Implementation

**Static HTML.** One self-contained file built by `html_document` from an `HtmlReport` (review-2.md has the reasons for each choice below).

- *Self-contained and offline.* plotly.js is inlined once, in one `<script>`, from `plotly.offline.get_plotlyjs()` (several MB); MathJax is not included. The page's CSS and script come from `templates/report.css` and `templates/report.js`, inlined; no attribute (`src`, `href`, `url(...)`) refers to anything outside the file, and no web font is used (system sans: `system-ui, -apple-system, "Segoe UI", sans-serif`). The file opens from disk with no network, and can be hosted on GitHub Pages or attached to an issue. The templates are read with `importlib.resources` and filled with stdlib `string.Template`; no templating library is added.
- *Escaping.* Every text from the data (logins, repository names, labels) reaches the page through `html.escape`. The figures and the client script's data are one JSON object in `<script type="application/json" id="wambatic-data">`, written with `json.dumps(..., ensure_ascii=False)` and then `<`, `>` and `&` replaced by `\u003c`, `\u003e` and `\u0026`, so no data can close the script element.
- *Layout*, in this order; a section appears only when the result has its group's series, as in the terminal:
  1. A header: `wambatic` and the subject (`repo octocat/Hello-World`), the range of the `TOTAL` result, the timezone (since 1.3 the terminal's `commits in authors' zones, other events in <timezone>` when `provenance['commit_timezone']` is `'author'`), and the granularity switch: a radio group Year, Month, Week, Day with `initial` checked.
  2. Summary tiles from the `TOTAL` result: Commits, Contributors (top-contributors rows other than `unattributed`), Lines added, Lines deleted and Net lines (signed) for `activity`; PRs opened, PRs merged, Issues opened, Issues closed and Median time to merge (hours, one decimal place; `-` with no value) for `flow`; Workflow runs, Success rate, Releases, and Deployments and Median lead time when those proxies are emitted, for `delivery`; Stars, Forks and Watchers (the sums of `tables['popularity']`) and Top language (the first row of `tables['languages']` other than `Other`, `-` when there is none) for `popularity`. Numbers are formatted as in the terminal.
  3. Activity: the per-period charts of `build_figures` for `activity`, the Commits by day calendar from the `DAY` result (not switched), the whole-range charts of `build_range_figures`, then the tables: Activity by period (one per granularity, all but the shown one `hidden`), By repository, By author and Top contributors (every row; the chart shows the first `TOP_CONTRIBUTORS_SHOWN`).
  4. Flow: the per-period charts of `build_figures` for `flow`, then Flow by period and Flow times by period, one table per granularity as above.
  5. Delivery: the per-period charts of `build_figures` for `delivery`, then Delivery by period and, when a proxy is emitted, DORA proxies by period, one table per granularity as above, with a line under the section heading that the DORA figures are proxies and how each is measured is in the README.
  6. Popularity: the per-period charts of `build_figures` for `popularity`, the Languages chart of `build_range_figures`, then Popularity by period (one table per granularity, as above), Popularity now and Languages (every row; the chart shows at most `TOP_LANGUAGES_SHOWN` bars, the last an `Other` bar summing the rest when there are more), with a line under the section heading that the counts are as of the last sync and the totals count the stars and forks that exist now.
  7. Unavailable, when `tables['unavailable']` is not empty.
  8. A provenance footer: the terminal's items (with its GitHub host line, 1.1, and its branch and excluded-files lines, 1.2), the plotly.js version (`plotly.offline.get_plotlyjs_version()`), and the `--ignore-cache-version` warning when `version_override_at` is present.
  Tables hold the same rows and columns as the terminal's, from `rows.py`, so the two never disagree; they are the page's data view and work without script.
- *Built once.* `html_document` builds each period's `build_figures`, the `build_range_figures` of the `TOTAL` result and the `build_calendar` of the `DAY` result once, and every part of the page (the chart elements, the sections, the embedded data) reads those; it never calls a builder a second time for the same result. A section's presence test reuses the table it then renders rather than building it to test for `None`. In `rows.py`, `figures.py` and `terminal.py` a function that needs a result's total series and bucket list derives each once and passes them on. The output is unchanged byte for byte: the existing HTML, terminal and JSON tests are the check.
- *Granularity switch.* All four period results are embedded as figures and pre-rendered tables. Choosing a granularity calls `Plotly.react` on each per-period chart with that granularity's figure and toggles the `hidden` attribute of the period tables; nothing is recomputed in the browser. Only total series are embedded per period (never the per-repo or per-author breakdowns, which would grow with repos times days); the breakdown charts and tables come from the `TOTAL` result.
- *Charts* (`build_figures`, per period, in this order): Commits, Contributors and Active days per period (bars, one each), Lines added and deleted per period (added as bars above zero and deleted as negative bars below it with `barmode='relative'`, net as a line on the same axis); Pull requests per period (grouped bars, opened and merged), Issues per period (grouped bars, opened and closed), Time to first review, Time to merge and Time to close (each a p50 and a p90 line, hours, a gap where a bucket has no value), PR size (p50 line, lines); Workflow runs per period (bars), Workflow success rate (line, 0 to 100 per cent on a fixed axis), Workflow duration (p50 and p90 lines, minutes), Releases per period (bars), Release interval (p50 line, days), then, each only when its series is present, Deployments per period (bars), Lead time (p50 and p90 lines, hours), Change failure rate (line, per cent on a fixed 0 to 100 axis) and Time to restore (p50 and p90 lines, hours); Stars per period (bars, `stars_added`), Stars over time (line, `stars_total`), Forks per period (bars, `forks_added`) and Forks over time (line, `forks_total`). Ratios are shown as percentages, the series' 0 to 1 values multiplied by 100. `build_range_figures`: Top contributors (horizontal bars of commits, first `TOP_CONTRIBUTORS_SHOWN`, largest at the top), By repository and By author (horizontal bars of commits, each when that breakdown is present, all-zero rows left out as in the terminal), and Languages (horizontal bars of each language's share in per cent, the rows of `tables['languages']` in its order, cut to `TOP_LANGUAGES_SHOWN` bars with one `Other` bar summing the rest when there are more, first row at the top; group `popularity`, present when the table is not empty). `build_calendar`: a heat-map of commits by day, one column per ISO week (x is the week's Monday) and one row per weekday, Monday at the top. Every chart has one y-axis; there are no dual axes.
- *Partial buckets.* Bars of a bucket in `provenance['partial_buckets']` carry a diagonal hatch (`marker.pattern.shape` `'/'`); line points in such a bucket have open markers; a chart with a partial bucket has the caption `hatched or open: partial period`.
- *Palette and themes.* Colours follow the validated reference palette of the dataviz skill (read 2026-10-30), held as `PALETTE` in `figures.py`: categorical slots 1 to 3, light `#2a78d6`, `#eb6834`, `#1baf7a`, dark `#3987e5`, `#d95926`, `#199e70` (no chart has more than three series, the most the palette validates for every pair); the heat-map's sequential blue ramp `#cde2fb`, `#86b6ef`, `#3987e5`, `#256abf`, `#0d366b` on light and `#104281`, `#1c5cab`, `#3987e5`, `#6da7ec`, `#b7d3f6` on dark (low to high, so more commits are brighter on the dark surface); chart surface `#fcfcfb` / `#1a1a19`, page `#f9f9f7` / `#0d0d0d`, primary ink `#0b0b0b` / `#f0efec`, secondary ink `#52514e` / `#c3c2b7`, gridlines `#e1e0d9` / `#2c2c2a`. Figures carry no colours: each trace has `meta: {"slot": n}` and the client script fills trace colours and layout colours from the active theme before each `Plotly.react`. `report.html_theme` `light` or `dark` sets `data-theme` on `<html>`; `auto` follows `prefers-color-scheme` and re-themes the charts when it changes. Text never wears a series colour.
- *Labels and hover.* A chart with one series has no legend (its title names it); with two or three it has a legend and each line is labelled at its last point. Hover shows each point's value (`hovermode='x unified'` on per-period charts). Each chart's element has `role="img"` and its `description` as `aria-label`.
- *Testing.* Unit tests validate every figure with `plotly.graph_objects.Figure(data=..., layout=...)`, which rejects an unknown property. A headless-browser test (`src/tests/reports/test_html_browser.py`, marker `browser`) opens the file from disk with [Playwright for Python](https://playwright.dev/python/) and Chromium, aborts and records every request that is not the file itself, and checks there is none, no console error and no page error, that every chart rendered, that each of the four granularities shows its own number of buckets, and that dark and light themes apply. It launches Playwright's own Chromium, else the cloud environment's preinstalled `/opt/pw-browsers/chromium`, else skips with that reason; CI's `browser` job installs Chromium with `playwright install --with-deps chromium` and runs it.

**Visualisation choices.** Line charts for trends, bars for per-bucket counts, stacked bars for added and deleted lines with net as an overlaid line, heat-map calendar for daily commit activity, horizontal bars for contributors and languages. Partial first and last buckets are hatched. The Static HTML paragraph above settles each (step 7, languages in step 10).
