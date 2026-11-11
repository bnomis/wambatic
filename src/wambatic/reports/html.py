"""The static HTML report: one self-contained file holding the summary, every chart and every
table, built from the results of one request that differ only in granularity."""

import collections.abc
import dataclasses
import functools
import html
import json
import os
import pathlib
import re
import string
import tempfile
import typing

import plotly.offline

import wambatic.reports.assets
import wambatic.reports.errors
import wambatic.reports.figures
import wambatic.reports.rows
import wambatic.reports.terminal
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.popularity

PERIODS = (
    wambatic.stats.base.Granularity.YEAR,
    wambatic.stats.base.Granularity.MONTH,
    wambatic.stats.base.Granularity.WEEK,
    wambatic.stats.base.Granularity.DAY,
)
SAFE_FILENAME = re.compile(r'[^A-Za-z0-9._-]')
FILE_MODE = 0o644
PROXIES_LINE = 'The DORA figures are proxies; how each is measured is described in the README.'
OTHER_LANGUAGE = wambatic.stats.popularity.OTHER
POPULARITY_LINE = 'Counts are as of the last sync; totals count the stars and forks that exist now.'
FORMAT_NET = functools.partial(wambatic.reports.terminal.format_number, signed=True)
JSON_ESCAPES = {'&': '\\u0026', '<': '\\u003c', '>': '\\u003e'}


@dataclasses.dataclass(frozen=True, slots=True)
class HtmlReport:
    """The five results one page is built from: `total` for the tiles, the whole-range charts
    and tables, and one result for each of year, month, week and day for the switch; `initial`
    is the granularity shown on load."""

    total: wambatic.stats.base.StatsResult
    periods: dict[wambatic.stats.base.Granularity, wambatic.stats.base.StatsResult]
    initial: wambatic.stats.base.Granularity


def period_requests(
    request: wambatic.stats.base.StatsRequest,
) -> list[wambatic.stats.base.StatsRequest]:
    """The five requests of a report: `request` with granularity TOTAL, then YEAR, MONTH, WEEK
    and DAY, everything else unchanged."""
    return [
        dataclasses.replace(request, granularity=granularity)
        for granularity in (wambatic.stats.base.Granularity.TOTAL, *PERIODS)
    ]


def html_report(
    results: list[wambatic.stats.base.StatsResult], initial: wambatic.stats.base.Granularity
) -> HtmlReport:
    """The `HtmlReport` of the five results of `period_requests`, in that order."""
    total, *periods = results
    return HtmlReport(
        total=total,
        periods={result.request.granularity: result for result in periods},
        initial=initial,
    )


class SubjectLike(typing.Protocol):
    """What `report_filename` reads of a `wambatic.fetch.base.Subject`, which `wambatic.reports` may
    not import."""

    @property
    def kind(self) -> str: ...

    @property
    def login(self) -> str: ...

    @property
    def full_name(self) -> str: ...


def report_filename(subject: SubjectLike) -> str:
    """`repo-OWNER-NAME.html`, `user-NAME.html` or `org-NAME.html`."""
    name = subject.full_name.replace('/', '-') if subject.kind == 'repo' else subject.login
    return f'{subject.kind}-{SAFE_FILENAME.sub("-", name)}.html'


def first_difference(
    total: wambatic.stats.base.StatsResult, other: wambatic.stats.base.StatsResult
) -> str | None:
    """The first thing, other than granularity, in which `other` was not made like `total`."""
    if total.subject != other.subject:
        return 'subject'
    for field in dataclasses.fields(wambatic.stats.base.StatsRequest):
        if field.name != 'granularity' and getattr(total.request, field.name) != getattr(
            other.request, field.name
        ):
            return f'request {field.name}'
    if total.until != other.until:
        return 'the resolved until'
    # Without a requested start each result begins at the start of the bucket holding the first
    # record, so the resolved starts differ by granularity by design.
    if total.request.since is not None and total.since != other.since:
        return 'the resolved since'
    return None


def check_report(report: HtmlReport) -> None:
    if report.total.request.granularity is not wambatic.stats.base.Granularity.TOTAL:
        raise wambatic.reports.errors.UsageError(
            f'total must be a TOTAL result, not {report.total.request.granularity}'
        )
    if set(report.periods) != set(PERIODS):
        raise wambatic.reports.errors.UsageError(
            f'periods must be exactly {", ".join(PERIODS)}, not '
            f'{", ".join(sorted(report.periods)) or "none"}'
        )
    if report.initial not in report.periods:
        raise wambatic.reports.errors.UsageError(
            f'initial must be one of {", ".join(PERIODS)}, not {report.initial}'
        )
    for granularity, result in report.periods.items():
        if result.request.granularity is not granularity:
            raise wambatic.reports.errors.UsageError(
                f'the {granularity} result is by {result.request.granularity}'
            )
        if (difference := first_difference(report.total, result)) is not None:
            raise wambatic.reports.errors.UsageError(
                f'the {granularity} result differs from the total in {difference}'
            )


def escape(text: object) -> str:
    return html.escape(str(text))


def json_for_script(data: object) -> str:
    """JSON that cannot close or open a script element, whatever the data holds."""
    text = json.dumps(data, ensure_ascii=False)
    return ''.join(JSON_ESCAPES.get(char, char) for char in text)


def theme_attribute(theme: wambatic.settings.Theme) -> str:
    """The `<html>` attribute that fixes a theme; `auto` leaves the choice to the viewer."""
    return '' if theme == 'auto' else f' data-theme="{theme}"'


@dataclasses.dataclass(frozen=True, slots=True)
class Number:
    """A numeric cell: the text shown and the value it was formatted from (None for no data)."""

    text: str
    value: float | None


def raw_value(value: float | None) -> str:
    """The `data-value` text: empty for no data, else the number with no needless `.0`."""
    if value is None:
        return ''
    if isinstance(value, float) and not value.is_integer():
        return repr(value)
    return str(int(value))


def number(format_text: collections.abc.Callable[[float], str], value: float | None) -> Number:
    """A cell for `value` shown as `format_text` gives it, or `-` for no data."""
    text = wambatic.reports.rows.NO_DATA if value is None else format_text(value)
    return Number(text, value)


def head_cell(text: str, numeric: bool) -> str:
    kind = 'number' if numeric else 'text'
    return f'<th{" class=num" if numeric else ""} data-type="{kind}">{escape(text)}</th>'


def cell(content: str | Number, numeric: bool) -> str:
    if isinstance(content, Number):
        return f'<td class=num data-value="{raw_value(content.value)}">{escape(content.text)}</td>'
    return f'<td{" class=num" if numeric else ""}>{escape(content)}</td>'


def table_html(
    title: str,
    headers: collections.abc.Sequence[str],
    rows: collections.abc.Sequence[collections.abc.Sequence[str | Number]],
    *,
    footer: collections.abc.Sequence[str | Number] | None = None,
    note: str = '',
    attributes: str = '',
    numeric: collections.abc.Sequence[bool] | None = None,
) -> str:
    """A data table whose first column is text and the others numbers, unless `numeric` says
    which columns are numbers. A numeric column holds `Number` cells carrying their raw value."""
    kinds = [i > 0 for i in range(len(headers))] if numeric is None else list(numeric)
    head = ''.join(head_cell(h, kinds[i]) for i, h in enumerate(headers))
    body = ''.join(
        '<tr>' + ''.join(cell(item, kinds[i]) for i, item in enumerate(row)) + '</tr>'
        for row in rows
    )
    foot = ''
    if footer is not None:
        foot = (
            '<tfoot><tr>'
            + ''.join(cell(item, kinds[i]) for i, item in enumerate(footer))
            + '</tr></tfoot>'
        )
    caption = escape(title) + (f'<span class="note">{escape(note)}</span>' if note else '')
    return (
        f'<div class="table-scroll"><table{attributes}><caption>{caption}</caption>'
        f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody>{foot}</table></div>'
    )


def period_numbers(
    metrics: collections.abc.Sequence[str], values: collections.abc.Sequence[float | None]
) -> list[Number]:
    """The cells of one period row; a ratio's value is the 0 to 100 percentage its text shows."""
    return [
        Number(
            wambatic.reports.terminal.format_cell(metric, value),
            None
            if value is None
            else value * 100
            if wambatic.reports.rows.DELIVERY_UNITS.get(metric) == 'ratio'
            else value,
        )
        for metric, value in zip(metrics, values, strict=True)
    ]


def period_table_html(
    table: wambatic.reports.rows.PeriodTable,
    granularity: wambatic.stats.base.Granularity,
    hidden: bool,
    note: str,
) -> str:
    rows: list[list[str | Number]] = [
        [
            row.label + (wambatic.reports.rows.PARTIAL_MARK if row.partial else ''),
            *period_numbers(table.metrics, row.values),
        ]
        for row in table.rows
    ]
    footer: list[str | Number] | None = None
    if table.total is not None:
        footer = [
            'Total',
            *period_numbers(table.metrics, table.total),
        ]
    attributes = f' class="period" data-granularity="{granularity}"' + (' hidden' if hidden else '')
    return table_html(
        table.title,
        ['Period', *table.headers],
        rows,
        footer=footer,
        note=note,
        attributes=attributes,
    )


def period_tables_html(
    report: HtmlReport,
    build: collections.abc.Callable[
        [wambatic.stats.base.StatsResult], wambatic.reports.rows.PeriodTable | None
    ],
    note: collections.abc.Callable[[wambatic.reports.rows.PeriodTable], str],
) -> str:
    """One table for each granularity, all but the initial one hidden."""
    pieces = []
    for granularity in PERIODS:
        table = build(report.periods[granularity])
        if table is not None:
            pieces.append(
                period_table_html(table, granularity, granularity != report.initial, note(table))
            )
    return ''.join(pieces)


def partial_note(table: wambatic.reports.rows.PeriodTable) -> str:
    return '* partial period' if table.has_partial else ''


def delivery_note(table: wambatic.reports.rows.PeriodTable) -> str:
    return wambatic.reports.terminal.delivery_caption(table, 'minutes and days')


def dora_note(table: wambatic.reports.rows.PeriodTable) -> str:
    return wambatic.reports.terminal.delivery_caption(table, 'proxies: see the README; hours')


def popularity_now_html(now: wambatic.reports.rows.PopularityNow | None) -> str:
    if now is None:
        return ''

    def texts(row: wambatic.reports.rows.PopularityRow) -> list[str | Number]:
        return [
            row.repo,
            *(
                number(wambatic.reports.terminal.format_number, count)
                for count in (row.stars, row.forks, row.watchers)
            ),
        ]

    return table_html(
        'Popularity now',
        wambatic.reports.rows.POPULARITY_NOW_HEADERS,
        [texts(row) for row in now.rows],
        footer=None if now.total is None else texts(now.total),
        note='as of the last sync; forks: whole network',
    )


def languages_html(languages: wambatic.reports.rows.Languages | None) -> str:
    if languages is None:
        return ''
    return table_html(
        'Languages',
        wambatic.reports.rows.LANGUAGE_HEADERS,
        [
            [
                row.language,
                number(wambatic.reports.terminal.format_number, row.bytes),
                number(lambda share: f'{share:,.1f}%', row.share * 100),
            ]
            for row in languages.rows
        ],
    )


def breakdown_html(result: wambatic.stats.base.StatsResult) -> str:
    pieces = []
    for kind, title in wambatic.reports.rows.BREAKDOWN_TITLES:
        rows = wambatic.reports.rows.breakdown_rows(result, kind)
        if rows is not None:
            pieces.append(
                table_html(
                    title,
                    wambatic.reports.rows.BREAKDOWN_HEADERS,
                    [
                        [
                            row.name,
                            number(wambatic.reports.terminal.format_number, row.commits),
                            number(wambatic.reports.terminal.format_number, row.lines_added),
                            number(wambatic.reports.terminal.format_number, row.lines_deleted),
                            number(FORMAT_NET, row.lines_net),
                        ]
                        for row in rows
                    ],
                )
            )
    return ''.join(pieces)


def contributors_html(result: wambatic.stats.base.StatsResult) -> str:
    rows = wambatic.reports.rows.top_contributors(result)
    if not rows:
        return ''
    return table_html(
        'Top contributors',
        wambatic.reports.rows.CONTRIBUTOR_HEADERS,
        [
            [
                row.login,
                number(wambatic.reports.terminal.format_number, row.commits),
                number(wambatic.reports.terminal.format_number, row.lines_added),
                number(wambatic.reports.terminal.format_number, row.lines_deleted),
                number(FORMAT_NET, row.lines_net),
                number(wambatic.reports.terminal.format_number, row.active_days),
            ]
            for row in rows
        ],
    )


def unavailable_html(result: wambatic.stats.base.StatsResult) -> str:
    rows = wambatic.reports.rows.unavailable_rows(result)
    if not rows:
        return ''
    return (
        '<section id="unavailable"><h2>Unavailable</h2>'
        + table_html(
            'Unavailable',
            wambatic.reports.rows.UNAVAILABLE_HEADERS,
            rows,
            numeric=(False, False),
        )
        + '</section>'
    )


def figure_html(figure: wambatic.reports.figures.Figure, wide: bool = False) -> str:
    """A chart's element: plotly.js draws into the `div`, which names the chart for assistive
    technology; the caption stays outside it so drawing does not remove it."""
    return (
        f'<figure class="chart{" wide" if wide else ""}" data-group="{figure.group}">'
        f'<div id="{escape(figure.key)}" class="plot" role="img" '
        f'aria-label="{escape(figure.description)}"></div>'
        f'<figcaption>{escape(figure.title)}</figcaption></figure>'
    )


@dataclasses.dataclass(frozen=True, slots=True)
class PageFigures:
    """Every figure of one page, each built once by `build_page_figures`."""

    periods: dict[wambatic.stats.base.Granularity, list[wambatic.reports.figures.Figure]]
    range_figures: list[wambatic.reports.figures.Figure]
    calendar: wambatic.reports.figures.Figure | None


def build_page_figures(report: HtmlReport) -> PageFigures:
    return PageFigures(
        periods={
            granularity: wambatic.reports.figures.build_figures(result)
            for granularity, result in report.periods.items()
        },
        range_figures=wambatic.reports.figures.build_range_figures(report.total),
        calendar=wambatic.reports.figures.build_calendar(
            report.periods[wambatic.stats.base.Granularity.DAY]
        ),
    )


def period_figures(report: HtmlReport, built: PageFigures) -> list[wambatic.reports.figures.Figure]:
    """One figure for each chart any granularity has, in page order, as the elements the page
    script draws into."""
    seen: dict[str, wambatic.reports.figures.Figure] = {}
    for granularity in (report.initial, *PERIODS):
        for figure in built.periods[granularity]:
            seen.setdefault(figure.key, figure)
    order = {chart.key: index for index, chart in enumerate(wambatic.reports.figures.CHARTS)}
    return sorted(seen.values(), key=lambda figure: order[figure.key])


def tile(label: str, value: str) -> str:
    return f'<div class="tile"><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'


def tiles_html(
    total: wambatic.stats.base.StatsResult,
    now: wambatic.reports.rows.PopularityNow | None,
    languages: wambatic.reports.rows.Languages | None,
) -> str:
    series = wambatic.reports.rows.total_series(total)
    format_number = wambatic.reports.terminal.format_number

    def value(metric: str) -> float | None:
        points = series.get(metric)
        return points[0][1] if points else None

    pieces = []
    if wambatic.reports.rows.has_activity(total):
        pieces += [
            tile('Commits', format_number(value('commits') or 0)),
            tile('Contributors', format_number(wambatic.reports.rows.contributor_count(total))),
            tile('Lines added', format_number(value('lines_added') or 0)),
            tile('Lines deleted', format_number(value('lines_deleted') or 0)),
            tile('Net lines', format_number(value('lines_net') or 0, signed=True)),
        ]
    if wambatic.reports.rows.has_flow(total):
        pieces += [
            tile('PRs opened', format_number(value('prs_opened') or 0)),
            tile('PRs merged', format_number(value('prs_merged') or 0)),
            tile('Issues opened', format_number(value('issues_opened') or 0)),
            tile('Issues closed', format_number(value('issues_closed') or 0)),
            tile(
                'Median time to merge (hours)',
                wambatic.reports.terminal.format_cell(
                    'time_to_merge_p50', value('time_to_merge_p50')
                ),
            ),
        ]
    if wambatic.reports.rows.has_delivery(total):
        format_cell = wambatic.reports.terminal.format_cell
        pieces += [
            tile('Workflow runs', format_number(value('workflow_runs') or 0)),
            tile(
                'Success rate', format_cell('workflow_success_rate', value('workflow_success_rate'))
            ),
            tile('Releases', format_number(value('release_count') or 0)),
        ]
        if 'deployments' in series:
            pieces.append(tile('Deployments', format_number(value('deployments') or 0)))
        if 'lead_time_p50' in series:
            pieces.append(
                tile(
                    'Median lead time (hours)', format_cell('lead_time_p50', value('lead_time_p50'))
                )
            )
    pieces += popularity_tiles(now, languages)
    return f'<dl class="tiles">{"".join(pieces)}</dl>' if pieces else ''


def popularity_tiles(
    now: wambatic.reports.rows.PopularityNow | None,
    languages: wambatic.reports.rows.Languages | None,
) -> list[str]:
    if now is None:
        return []
    format_number = wambatic.reports.terminal.format_number
    sums = now.total or (now.rows[0] if now.rows else wambatic.reports.rows.PopularityRow.empty())
    named = (
        [row.language for row in languages.rows if row.language != OTHER_LANGUAGE]
        if languages
        else []
    )
    top = named[0] if named else '-'
    return [
        tile('Stars', format_number(sums.stars)),
        tile('Forks', format_number(sums.forks)),
        tile('Watchers', format_number(sums.watchers)),
        tile('Top language', top),
    ]


def header_html(report: HtmlReport) -> str:
    total = report.total
    subject = wambatic.reports.rows.subject_text(total)
    switch = ''.join(
        f'<label><input type="radio" name="granularity" value="{granularity}"'
        f'{" checked" if granularity == report.initial else ""}> {granularity.title()}</label>'
        for granularity in PERIODS
    )
    return (
        '<header>'
        f'<h1>wambatic <span class="subject">{escape(subject)}</span></h1>'
        f'<p class="range">{escape(total.since)} to {escape(total.until)}, '
        f'{escape(wambatic.reports.rows.timezone_text(total))}</p>'
        f'<fieldset class="switch"><legend>Period</legend>{switch}</fieldset>'
        '</header>'
    )


def footer_html(total: wambatic.stats.base.StatsResult) -> str:
    lines = [
        *wambatic.reports.rows.provenance_lines(total),
        f'plotly.js: {plotly.offline.get_plotlyjs_version()}',
    ]
    return (
        '<footer>'
        + ''.join(
            f'<p{" class=warning" if line.startswith("Warning:") else ""}>{escape(line)}</p>'
            for line in lines
        )
        + '</footer>'
    )


def sections_html(
    report: HtmlReport,
    built: PageFigures,
    now: wambatic.reports.rows.PopularityNow | None,
    languages: wambatic.reports.rows.Languages | None,
) -> str:
    total = report.total
    figures = period_figures(report, built)
    range_figures = built.range_figures
    calendar = built.calendar
    sections = []
    if wambatic.reports.rows.activity_table(total) is not None:
        charts = [f for f in figures if f.group == 'activity']
        wide = [calendar] if calendar is not None else []
        pieces = [
            '<section id="activity"><h2>Activity</h2>',
            '<div class="charts">',
            *(figure_html(f) for f in charts),
            *(figure_html(f, True) for f in wide),
            *(figure_html(f) for f in range_figures if f.group == 'activity'),
            '</div>',
            period_tables_html(report, wambatic.reports.rows.activity_table, partial_note),
            breakdown_html(total),
            contributors_html(total),
            '</section>',
        ]
        sections.append(''.join(pieces))
    if wambatic.reports.rows.flow_table(total) is not None:
        pieces = [
            '<section id="flow"><h2>Flow</h2>',
            '<div class="charts">',
            *(figure_html(f) for f in figures if f.group == 'flow'),
            '</div>',
            period_tables_html(report, wambatic.reports.rows.flow_table, partial_note),
            period_tables_html(
                report,
                wambatic.reports.rows.flow_times_table,
                wambatic.reports.terminal.flow_times_caption,
            ),
            '</section>',
        ]
        sections.append(''.join(pieces))
    if wambatic.reports.rows.delivery_table(total) is not None:
        has_dora = wambatic.reports.rows.dora_table(total) is not None
        pieces = [
            '<section id="delivery"><h2>Delivery</h2>',
            f'<p class="proxies">{escape(PROXIES_LINE)}</p>' if has_dora else '',
            '<div class="charts">',
            *(figure_html(f) for f in figures if f.group == 'delivery'),
            '</div>',
            period_tables_html(report, wambatic.reports.rows.delivery_table, delivery_note),
            period_tables_html(report, wambatic.reports.rows.dora_table, dora_note),
            '</section>',
        ]
        sections.append(''.join(pieces))
    if wambatic.reports.rows.popularity_table(total) is not None:
        pieces = [
            '<section id="popularity"><h2>Popularity</h2>',
            f'<p class="popularity-note">{escape(POPULARITY_LINE)}</p>',
            '<div class="charts">',
            *(figure_html(f) for f in figures if f.group == 'popularity'),
            *(figure_html(f) for f in range_figures if f.group == 'popularity'),
            '</div>',
            period_tables_html(
                report,
                wambatic.reports.rows.popularity_table,
                wambatic.reports.terminal.popularity_caption,
            ),
            popularity_now_html(now),
            languages_html(languages),
            '</section>',
        ]
        sections.append(''.join(pieces))
    sections.append(unavailable_html(total))
    return ''.join(sections)


def page_data(
    report: HtmlReport, theme: wambatic.settings.Theme, built: PageFigures
) -> dict[str, object]:
    calendar = built.calendar
    return {
        'initial': str(report.initial),
        'theme': theme,
        'palette': {
            name: dataclasses.asdict(colours)
            for name, colours in wambatic.reports.figures.PALETTE.items()
        },
        'periods': {
            str(granularity): [dataclasses.asdict(f) for f in figures]
            for granularity, figures in built.periods.items()
        },
        'range': [dataclasses.asdict(f) for f in built.range_figures],
        'calendar': None if calendar is None else dataclasses.asdict(calendar),
    }


def asset_tags(assets_url: str) -> tuple[str, str]:
    """The stylesheet link and the script elements for the files under `assets_url`."""
    link = (
        f'<link rel="stylesheet" href="{escape(assets_url)}'
        f'{wambatic.reports.assets.STYLESHEET_NAME}">'
    )
    scripts = '\n'.join(
        f'<script defer src="{escape(assets_url)}{name}"></script>'
        for name in wambatic.reports.assets.SCRIPT_NAMES
    )
    return link, scripts


def html_document(report: HtmlReport, theme: wambatic.settings.Theme, assets_url: str) -> str:
    """The whole page, which loads its scripts and stylesheet from `assets_url`, a URL path ending
    in `/`. Pure: the only reads are of this package's templates and assets.
    Raises UsageError when the five results differ in anything but granularity."""
    check_report(report)
    built = build_page_figures(report)
    now = wambatic.reports.rows.popularity_now(report.total)
    languages = wambatic.reports.rows.languages_rows(report.total)
    title = f'wambatic: {wambatic.reports.rows.subject_text(report.total)}'
    link, scripts = asset_tags(assets_url)
    return string.Template(wambatic.reports.assets.read_template('report.html')).substitute(
        theme_attribute=theme_attribute(theme),
        title=escape(title),
        stylesheet=link,
        header=header_html(report),
        missing=missing_assets_html(),
        tiles=tiles_html(report.total, now, languages),
        sections=sections_html(report, built, now, languages),
        footer=footer_html(report.total),
        data=json_for_script(page_data(report, theme, built)),
        scripts=scripts,
    )


def missing_assets_html() -> str:
    """The notice shown when the page's folder did not load; only the stylesheet hides it."""
    return (
        '<p class="assets-missing">'
        f"This report's files ({escape(wambatic.reports.assets.assets_folder_name())}) "
        'did not load; keep the page beside that folder.</p>'
    )


def render_html(
    report: HtmlReport, out: pathlib.Path, theme: wambatic.settings.Theme
) -> pathlib.Path:
    """Write the assets folder beside `out`, then `html_document(report, theme, ...)` to `out`,
    and return `out`. The page is written to a temporary file beside `out` and moved into place,
    so a failed write leaves `out` as it was and no temporary file behind; it is not written when
    the folder cannot be. Missing parent directories are created. Raises OutputError when either
    cannot be written."""
    document = html_document(report, theme, f'{wambatic.reports.assets.assets_folder_name()}/')
    wambatic.reports.assets.write_assets(out.parent)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            'w', encoding='utf-8', dir=out.parent, suffix='.tmp', delete=False
        ) as handle:
            temporary = pathlib.Path(handle.name)
            try:
                handle.write(document)
                handle.flush()
                temporary.chmod(FILE_MODE)
                os.replace(temporary, out)
            except BaseException:
                # Cleans up the temporary file, then re-raises the original error.
                temporary.unlink(missing_ok=True)
                raise
    except OSError as e:
        # auditme: accept[except-interpolation] the OS reason says what to fix
        raise wambatic.reports.errors.OutputError(f'cannot write {out}: {e.strerror or e}') from e
    return out
