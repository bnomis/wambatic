import collections.abc
import dataclasses
import html.parser
import importlib.resources
import json
import os
import pathlib
import re
import stat

import plotly.offline
import pytest

import tests.conftest
import tests.fixtures.reports
import tests.fixtures.stats
import wambatic.fetch.base
import wambatic.reports.assets
import wambatic.reports.errors
import wambatic.reports.figures
import wambatic.reports.html
import wambatic.settings
import wambatic.stats.base

PERIOD_NAMES = ('day', 'month', 'week', 'year')
HOSTILE = '<b>&"\'</script>'
ASSETS_URL = 'assets/'


def html_document(
    report: wambatic.reports.html.HtmlReport, theme: wambatic.settings.Theme = 'auto'
) -> str:
    return wambatic.reports.html.html_document(report, theme, ASSETS_URL)


def without_values(document: str) -> str:
    """The page without its `data-value` attributes, to compare the markup of the shown text."""
    return re.sub(r' data-value="[^"]*"', '', document)


class Page(html.parser.HTMLParser):
    """The parts of a report page the tests look at."""

    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.tiles: dict[str, str] = {}
        self.data = ''
        self.style = ''
        self.text = ''
        self.open: list[tuple[str, dict[str, str | None]]] = []
        self.label = ''
        self.feed(text)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))
        if tag not in ('input', 'meta', 'br'):
            self.open.append((tag, dict(attrs)))

    def handle_endtag(self, tag: str) -> None:
        while self.open and self.open.pop()[0] != tag:
            pass

    def handle_data(self, data: str) -> None:
        if not self.open:
            return
        tag, attrs = self.open[-1]
        if tag == 'script':
            if attrs.get('id') == 'wambatic-data':
                self.data += data
        elif tag == 'style':
            self.style += data
        else:
            self.text += data
            if tag == 'dt':
                self.label = data
            elif tag == 'dd':
                self.tiles[self.label] = data

    def by_id(self, key: str) -> dict[str, str | None]:
        matches = [attrs for _, attrs in self.elements if attrs.get('id') == key]
        assert len(matches) == 1, key
        return matches[0]

    def tables(self) -> list[dict[str, str | None]]:
        return [attrs for tag, attrs in self.elements if tag == 'table']


def keys_of(report: wambatic.reports.html.HtmlReport) -> set[str]:
    keys: set[str] = set()
    for result in report.periods.values():
        keys |= {f.key for f in wambatic.reports.figures.build_figures(result)}
    keys |= {f.key for f in wambatic.reports.figures.build_range_figures(report.total)}
    calendar = wambatic.reports.figures.build_calendar(
        report.periods[wambatic.stats.base.Granularity.DAY]
    )
    assert calendar is not None
    return keys | {calendar.key}


def test_every_figure_has_its_element_naming_the_chart(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    page = Page(html_document(org_report, 'auto'))
    keys = keys_of(org_report)
    assert 'activity-commits' in keys
    assert 'activity-calendar' in keys
    assert 'activity-by-author' in keys
    assert 'flow-merge-time' in keys
    for key in keys:
        element = page.by_id(key)
        assert element['role'] == 'img'
        assert element['aria-label']


def test_the_figures_of_every_granularity_are_in_the_embedded_data(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    page = Page(html_document(org_report, 'dark'))
    data = json.loads(page.data)
    assert data['initial'] == 'month'
    assert data['theme'] == 'dark'
    assert sorted(data['periods']) == list(PERIOD_NAMES)
    months = data['periods']['month'][0]['data'][0]['x']
    assert months == list(tests.fixtures.stats.LABELS)
    assert data['calendar']['key'] == 'activity-calendar'
    assert [f['key'] for f in data['range']] == list(tests.fixtures.reports.RANGE_FIGURE_KEYS)
    assert data['palette']['light']['categorical'] == ['#2a78d6', '#eb6834', '#1baf7a']
    assert set(data['palette']) == {'light', 'dark'}


def test_period_tables_appear_once_per_granularity_with_only_the_initial_one_visible(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    page = Page(html_document(org_report, 'auto'))
    periods = [t for t in page.tables() if t.get('class') == 'period']
    seen: dict[str, list[str | None]] = {}
    for table in periods:
        granularity = table['data-granularity']
        assert granularity is not None
        seen.setdefault(granularity, []).append('hidden' if 'hidden' in table else None)
    assert sorted(seen) == list(PERIOD_NAMES)
    assert all(len(hidden) == 3 for hidden in seen.values())  # activity, flow, flow times
    visible = {g for g, hidden in seen.items() if hidden[0] is None}
    assert visible == tests.fixtures.reports.MONTH_ONLY
    assert all(h is None for h in seen['month'])
    assert all(h == 'hidden' for g, hidden in seen.items() if g != 'month' for h in hidden)
    other = Page(
        html_document(
            dataclasses.replace(org_report, initial=wambatic.stats.base.Granularity.DAY), 'auto'
        )
    )
    day_tables = [t for t in other.tables() if t.get('data-granularity') == 'day']
    assert all('hidden' not in t for t in day_tables)


def test_the_initial_granularitys_radio_is_checked(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    page = Page(html_document(org_report, 'auto'))
    radios = {
        attrs['value']: 'checked' in attrs
        for tag, attrs in page.elements
        if tag == 'input' and attrs.get('name') == 'granularity'
    }
    assert radios == {'year': False, 'month': True, 'week': False, 'day': False}


def test_the_tiles_show_the_totals(org_report: wambatic.reports.html.HtmlReport) -> None:
    page = Page(html_document(org_report, 'auto'))
    assert page.tiles['Commits'] == '10'
    assert page.tiles['Contributors'] == '3'
    assert page.tiles['Lines added'] == '90'
    assert page.tiles['Lines deleted'] == '48'
    assert page.tiles['Net lines'] == '+42'
    assert page.tiles['PRs opened'] == '10'
    assert page.tiles['PRs merged'] == '7'
    assert page.tiles['Issues opened'] == '5'
    assert page.tiles['Issues closed'] == '4'


def test_a_median_with_no_data_is_a_dash(org_report: wambatic.reports.html.HtmlReport) -> None:
    series = [
        dataclasses.replace(s, points={}) if s.metric == 'time_to_merge_p50' else s
        for s in org_report.total.series
    ]
    report = dataclasses.replace(
        org_report, total=dataclasses.replace(org_report.total, series=series)
    )
    page = Page(html_document(report, 'auto'))
    assert page.tiles['Median time to merge (hours)'] == '-'
    whole = Page(html_document(org_report, 'auto'))
    assert whole.tiles['Median time to merge (hours)'] != '-'


def test_the_period_tables_hold_the_terminals_rows(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = without_values(html_document(org_report, 'auto'))
    assert '<td>2026-10</td><td class=num>7</td><td class=num>3</td>' in document
    assert '<td>Total</td><td class=num>10</td><td class=num>3</td>' in document
    assert '<td class=num>+34</td>' in document
    assert 'Flow times by period' in document
    assert '<td class=num>-</td>' in document


def test_the_document_holds_no_copy_of_plotly_js_but_names_its_version(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    assert f'plotly.js v{plotly.offline.get_plotlyjs_version()}' not in document
    assert f'plotly.js: {plotly.offline.get_plotlyjs_version()}' in document


def test_the_page_names_only_files_under_the_assets_url(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    page = Page(html_document(org_report, 'auto'))
    for _, attrs in page.elements:
        for name in ('src', 'href', 'action'):
            value = attrs.get(name)
            if value is not None:
                assert not value.startswith(('http:', 'https:', '//')), (name, value)
    files = [
        value
        for tag, attrs in page.elements
        for name in ('src', 'href')
        if tag in ('link', 'script') and (value := attrs.get(name))
    ]
    assert sorted(files) == sorted(
        f'{ASSETS_URL}{asset.name}' for asset in wambatic.reports.assets.page_assets()
    )
    assert page.style == ''


def test_the_scripts_load_deferred_in_order_after_the_page_data(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    positions = [
        document.index(f'<script defer src="{ASSETS_URL}{name}"></script>')
        for name in ('plotly.min.js', 'write-excel-file.min.js', 'tables.js', 'report.js')
    ]
    assert positions == sorted(positions)
    assert document.index('id="wambatic-data"') < positions[0]
    assert f'<link rel="stylesheet" href="{ASSETS_URL}report.css">' in document


def test_a_page_says_what_to_do_when_its_folder_did_not_load(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    folder = wambatic.reports.assets.assets_folder_name()
    assert (
        f'<p class="assets-missing">This report\'s files ({folder}) did not load; '
        'keep the page beside that folder.</p>'
    ) in document
    assert document.index('assets-missing') < document.index('<main>')
    assert '.assets-missing' in wambatic.reports.assets.stylesheet()


def test_a_hostile_login_is_escaped_in_the_html_and_round_trips_in_the_data(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    rows = [{**tests.fixtures.stats.ORG_TOP_CONTRIBUTORS[0], 'login': HOSTILE}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'top_contributors': rows}
    )
    document = html_document(dataclasses.replace(org_report, total=total), 'auto')
    assert HOSTILE not in document
    assert '&lt;b&gt;&amp;&quot;&#x27;&lt;/script&gt;' in document
    page = Page(document)
    data = json.loads(page.data)
    assert data['range'][0]['data'][0]['y'] == [HOSTILE]
    assert '<' not in page.data
    assert '\\u003c/script\\u003e' in page.data


def test_hostile_labels_in_the_other_tables_are_escaped(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    unavailable = [{'metric': HOSTILE, 'reason': HOSTILE}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'unavailable': unavailable}
    )
    document = html_document(dataclasses.replace(org_report, total=total), 'auto')
    assert HOSTILE not in document
    assert document.count('&lt;b&gt;&amp;&quot;&#x27;&lt;/script&gt;') == 2


def test_the_embedded_data_is_valid_json_with_unicode_kept(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    rows = [{**tests.fixtures.stats.ORG_TOP_CONTRIBUTORS[0], 'login': 'zoë'}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'top_contributors': rows}
    )
    page = Page(html_document(dataclasses.replace(org_report, total=total), 'auto'))
    assert json.loads(page.data)['range'][0]['data'][0]['y'] == ['zoë']


@pytest.mark.parametrize(
    ('subject', 'name'),
    [
        (wambatic.fetch.base.Subject('repo', 'octo-org', 'alpha'), 'repo-octo-org-alpha.html'),
        (wambatic.fetch.base.Subject('user', 'octocat'), 'user-octocat.html'),
        (wambatic.fetch.base.Subject('org', 'octo-org'), 'org-octo-org.html'),
        (wambatic.fetch.base.Subject('repo', 'o', '.github'), 'repo-o-.github.html'),
        (wambatic.fetch.base.Subject('repo', 'o', 'a/../b'), 'repo-o-a-..-b.html'),
    ],
)
def test_report_filename_names_the_kind_and_the_subject(
    subject: wambatic.fetch.base.Subject, name: str
) -> None:
    assert wambatic.reports.html.report_filename(subject) == name


def test_a_total_that_is_not_total_is_refused(org_report: wambatic.reports.html.HtmlReport) -> None:
    month = org_report.periods[wambatic.stats.base.Granularity.MONTH]
    with pytest.raises(wambatic.reports.errors.UsageError, match='total must be a TOTAL result'):
        html_document(dataclasses.replace(org_report, total=month), 'auto')


def test_a_missing_granularity_is_refused(org_report: wambatic.reports.html.HtmlReport) -> None:
    periods: dict[wambatic.stats.base.Granularity, wambatic.stats.base.StatsResult] = {
        g: r for g, r in org_report.periods.items() if g is not wambatic.stats.base.Granularity.WEEK
    }
    with pytest.raises(wambatic.reports.errors.UsageError, match='periods must be exactly'):
        html_document(dataclasses.replace(org_report, periods=periods), 'auto')


def test_an_initial_granularity_outside_the_periods_is_refused(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    with pytest.raises(wambatic.reports.errors.UsageError, match='initial'):
        html_document(
            dataclasses.replace(org_report, initial=wambatic.stats.base.Granularity.TOTAL), 'auto'
        )


def test_results_without_a_requested_start_begin_at_their_own_period_start_and_build_a_page(
    stats_fetcher: wambatic.fetch.base.Fetcher,
) -> None:
    request = wambatic.stats.base.StatsRequest(until=tests.fixtures.stats.UNTIL)
    results = [
        tests.conftest.run_stats(stats_fetcher, tests.fixtures.stats.ORG, item)
        for item in wambatic.reports.html.period_requests(request)
    ]
    starts = {result.since for result in results}
    assert len(starts) > 1
    report = wambatic.reports.html.html_report(results, wambatic.stats.base.Granularity.MONTH)
    assert 'id="wambatic-data"' in html_document(report, 'auto')


def test_a_result_made_for_another_range_is_refused_naming_the_difference(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    month = org_report.periods[wambatic.stats.base.Granularity.MONTH]
    other = dataclasses.replace(
        month,
        request=dataclasses.replace(month.request, since=tests.fixtures.stats.SINCE.replace(day=2)),
    )
    periods = {**org_report.periods, wambatic.stats.base.Granularity.MONTH: other}
    with pytest.raises(
        wambatic.reports.errors.UsageError,
        match='month result differs from the total in request since',
    ):
        html_document(dataclasses.replace(org_report, periods=periods), 'auto')


def test_a_result_for_another_subject_or_groups_is_refused(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    day = org_report.periods[wambatic.stats.base.Granularity.DAY]
    user = dataclasses.replace(day, subject=wambatic.fetch.base.Subject('user', 'octocat'))
    with pytest.raises(
        wambatic.reports.errors.UsageError, match='day result differs from the total in subject'
    ):
        html_document(
            dataclasses.replace(
                org_report,
                periods={**org_report.periods, wambatic.stats.base.Granularity.DAY: user},
            ),
            'auto',
        )
    groups = dataclasses.replace(
        day, request=dataclasses.replace(day.request, groups=tests.fixtures.stats.GROUP_ACTIVITY)
    )
    with pytest.raises(wambatic.reports.errors.UsageError, match='request groups'):
        html_document(
            dataclasses.replace(
                org_report,
                periods={**org_report.periods, wambatic.stats.base.Granularity.DAY: groups},
            ),
            'auto',
        )


def test_a_result_filed_under_the_wrong_granularity_is_refused(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    periods = {
        **org_report.periods,
        wambatic.stats.base.Granularity.WEEK: org_report.periods[
            wambatic.stats.base.Granularity.DAY
        ],
    }
    with pytest.raises(wambatic.reports.errors.UsageError, match='week result is by day'):
        html_document(dataclasses.replace(org_report, periods=periods), 'auto')


@pytest.mark.parametrize(
    ('theme', 'attribute'), [('light', 'light'), ('dark', 'dark'), ('auto', None)]
)
def test_each_theme_sets_data_theme_on_the_html_element_as_it_should(
    org_report: wambatic.reports.html.HtmlReport,
    theme: wambatic.settings.Theme,
    attribute: str | None,
) -> None:
    page = Page(html_document(org_report, theme))
    html_attributes = next(attrs for tag, attrs in page.elements if tag == 'html')
    assert html_attributes.get('data-theme') == attribute


def test_the_stylesheet_defines_both_themes_as_custom_properties() -> None:
    style = wambatic.reports.assets.stylesheet()
    assert '--surface: #fcfcfb;' in style
    assert '--surface: #1a1a19;' in style
    assert ':root[data-theme="dark"]' in style
    assert 'prefers-color-scheme: dark' in style
    assert style.count('--series-1: #3987e5;') == 2
    assert re.search(r'--sequential-5: #b7d3f6;', style)


def test_a_repo_page_has_no_by_repository_table_and_the_sections_of_its_groups(
    repo_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(repo_report, 'auto')
    assert 'By repository' not in document
    assert 'id="tab-commits"' in document
    assert 'id="tab-flow"' in document
    assert 'repo octo-org/alpha' in document


def test_a_group_the_result_lacks_has_no_section(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    def flow_free(result: wambatic.stats.base.StatsResult) -> wambatic.stats.base.StatsResult:
        return dataclasses.replace(
            result,
            series=[
                s
                for s in result.series
                if s.metric.startswith(('commits', 'contributors', 'active', 'lines'))
            ],
        )

    report = wambatic.reports.html.HtmlReport(
        total=flow_free(org_report.total),
        periods={g: flow_free(r) for g, r in org_report.periods.items()},
        initial=org_report.initial,
    )
    document = html_document(report, 'auto')
    assert 'id="tab-commits"' in document
    assert 'id="tab-flow"' not in document
    assert panel_ids(document) == ACTIVITY_PANELS
    assert 'PRs opened' not in document


def test_the_templates_are_found_through_importlib_resources() -> None:
    templates = importlib.resources.files('wambatic.reports') / 'templates'
    for name in wambatic.reports.assets.TEMPLATE_NAMES:
        assert (templates / name).is_file()


def test_the_report_names_the_range_the_timezone_and_the_provenance(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    assert '2026-10-01 to 2027-01-31, UTC' in document
    assert 'computed_at: 2027-01-20T12:00:00+00:00' in document
    assert 'schema_version: ' in document
    warned = dataclasses.replace(
        org_report.total,
        provenance={
            **org_report.total.provenance,
            'version_override_at': '2027-01-20T12:00:00+00:00',
        },
    )
    assert 'ignore-cache-version' in html_document(
        dataclasses.replace(org_report, total=warned), 'auto'
    )


def test_the_header_names_both_zones_in_author_mode_only(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    def document(mode: str) -> str:
        total = dataclasses.replace(
            org_report.total, provenance={**org_report.total.provenance, 'commit_timezone': mode}
        )
        return html_document(dataclasses.replace(org_report, total=total), 'auto')

    assert '2026-10-01 to 2027-01-31, commits in authors&#x27; zones, other events in UTC' in (
        document('author')
    )
    assert '2026-10-01 to 2027-01-31, UTC' in document('report')
    keyless = dataclasses.replace(
        org_report.total,
        provenance={k: v for k, v in org_report.total.provenance.items() if k != 'commit_timezone'},
    )
    assert '2026-10-01 to 2027-01-31, UTC' in html_document(
        dataclasses.replace(org_report, total=keyless), 'auto'
    )


def test_the_commit_dates_unavailable_row_appears_in_the_html_report(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    rows = [{'metric': 'commit dates: octo-org/alpha', 'reason': 'dated in UTC: no author offset'}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'unavailable': rows}
    )
    document = html_document(dataclasses.replace(org_report, total=total), 'auto')
    assert 'commit dates: octo-org/alpha' in document


def test_the_footer_names_an_enterprise_host_and_github_com_is_unchanged(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    plain = html_document(org_report, 'auto')
    assert 'GitHub host' not in plain
    dotcom = dataclasses.replace(
        org_report.total, provenance={**org_report.total.provenance, 'github_host': 'github.com'}
    )
    assert html_document(dataclasses.replace(org_report, total=dotcom), 'auto') == plain
    enterprise = dataclasses.replace(
        org_report.total,
        provenance={
            **org_report.total.provenance,
            'github_host': 'ghe.example.com',
            'server_version': '3.19.1',
        },
    )
    document = html_document(dataclasses.replace(org_report, total=enterprise), 'auto')
    assert '<p>GitHub host: ghe.example.com (Enterprise Server 3.19.1)</p>' in document


def test_the_footer_says_how_commits_were_read(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    assert '<p>Commits read by: local clone</p>' in document
    assert '<p>Branches: default branch</p>' in document
    assert '; linguist-generated and linguist-vendored files</p>' in document
    set_up = dataclasses.replace(
        org_report.total,
        provenance={
            **org_report.total.provenance,
            'commit_methods': 'api-files',
            'branches': '["release/*"]',
            'exclude_paths': '[]',
            'linguist': 'false',
        },
    )
    document = html_document(dataclasses.replace(org_report, total=set_up), 'auto')
    assert '<p>Commits read by: API with files</p>' in document
    assert '<p>Branches: default branch and release/*</p>' in document
    assert '<p>Line counts leave out: nothing</p>' in document
    unread = dataclasses.replace(
        org_report.total,
        provenance={k: v for k, v in org_report.total.provenance.items() if k != 'commit_methods'},
    )
    document = html_document(dataclasses.replace(org_report, total=unread), 'auto')
    assert 'Commits read by' not in document


def test_render_html_writes_the_document_and_returns_the_path(
    org_report: wambatic.reports.html.HtmlReport, tmp_path: pathlib.Path
) -> None:
    out = tmp_path / 'out' / 'report.html'
    assert wambatic.reports.html.render_html(org_report, out, 'light') is out
    folder = wambatic.reports.assets.assets_folder_name()
    assert out.read_text(encoding='utf-8') == wambatic.reports.html.html_document(
        org_report, 'light', f'{folder}/'
    )
    assert sorted(path.name for path in out.parent.iterdir()) == sorted(
        [*tests.fixtures.reports.REPORT_FILES, folder]
    )
    assert sorted(path.name for path in (out.parent / folder).iterdir()) == sorted(
        asset.name for asset in wambatic.reports.assets.page_assets()
    )
    assert stat.S_IMODE(out.stat().st_mode) == 0o644


def test_a_second_render_replaces_the_file(
    org_report: wambatic.reports.html.HtmlReport,
    repo_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
) -> None:
    out = tmp_path / 'report.html'
    wambatic.reports.html.render_html(org_report, out, 'auto')
    wambatic.reports.html.render_html(repo_report, out, 'dark')
    text = out.read_text(encoding='utf-8')
    assert 'repo octo-org/alpha' in text
    assert 'org octo-org' not in text
    assert 'data-theme="dark"' in text


def test_missing_parent_directories_are_created(
    org_report: wambatic.reports.html.HtmlReport, tmp_path: pathlib.Path
) -> None:
    out = tmp_path / 'a' / 'b' / 'report.html'
    wambatic.reports.html.render_html(org_report, out, 'auto')
    assert out.is_file()


def test_a_failed_move_leaves_the_file_as_it_was_and_no_temporary_file(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / 'out'
    out = directory / 'report.html'

    def refuse(source: object, destination: object) -> None:
        raise OSError('no space left')

    with monkeypatch.context() as patch:
        patch.setattr(os, 'replace', refuse)
        with pytest.raises(wambatic.reports.errors.OutputError, match='no space left'):
            wambatic.reports.html.render_html(org_report, out, 'auto')
    assert [path.name for path in directory.iterdir()] == [
        wambatic.reports.assets.assets_folder_name()
    ]
    out.write_text('earlier')
    with monkeypatch.context() as patch:
        patch.setattr(os, 'replace', refuse)
        with pytest.raises(wambatic.reports.errors.OutputError, match='no space left'):
            wambatic.reports.html.render_html(org_report, out, 'auto')
    assert out.read_text() == 'earlier'
    assert sorted(path.name for path in directory.iterdir()) == sorted(
        [*tests.fixtures.reports.REPORT_FILES, wambatic.reports.assets.assets_folder_name()]
    )


def test_a_bad_report_writes_nothing(
    org_report: wambatic.reports.html.HtmlReport, tmp_path: pathlib.Path
) -> None:
    bad = dataclasses.replace(org_report, initial=wambatic.stats.base.Granularity.TOTAL)
    out = tmp_path / 'sub' / 'report.html'
    with pytest.raises(wambatic.reports.errors.UsageError, match='initial'):
        wambatic.reports.html.render_html(bad, out, 'auto')
    assert not out.parent.exists()


def only_delivery(
    report: wambatic.reports.html.HtmlReport, keep: collections.abc.Callable[[str], bool]
) -> wambatic.reports.html.HtmlReport:
    """`report` with only the series whose metric `keep` accepts."""

    def trimmed(result: wambatic.stats.base.StatsResult) -> wambatic.stats.base.StatsResult:
        return dataclasses.replace(result, series=[s for s in result.series if keep(s.metric)])

    return wambatic.reports.html.HtmlReport(
        total=trimmed(report.total),
        periods={g: trimmed(r) for g, r in report.periods.items()},
        initial=report.initial,
    )


def test_the_delivery_section_and_tiles_appear_only_with_delivery_series(
    org_report: wambatic.reports.html.HtmlReport,
    delivery_report: wambatic.reports.html.HtmlReport,
) -> None:
    without = html_document(org_report, 'auto')
    assert 'id="tab-delivery"' not in without
    assert 'Workflow runs' not in Page(without).tiles
    page = Page(html_document(delivery_report, 'auto'))
    assert page.by_id('tab-delivery')
    assert page.tiles['Workflow runs'] == '13'
    assert page.tiles['Success rate'] == '66.7%'  # 6 of 9 completed runs
    assert page.tiles['Releases'] == '6'
    assert page.tiles['Deployments'] == '5'
    assert page.tiles['Median lead time (hours)'] != '-'
    assert page.tiles['Commits'] == '10'


def test_every_delivery_figure_has_its_element_and_the_section_holds_its_charts(
    delivery_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(delivery_report, 'auto')
    page = Page(document)
    keys = {
        f.key
        for result in delivery_report.periods.values()
        for f in wambatic.reports.figures.build_figures(result)
        if f.group == 'delivery'
    }
    assert 'delivery-lead-time' in keys
    for key in keys:
        assert page.by_id(key)['role'] == 'img'
    section = document.split('id="tab-delivery"')[1].split('</section>')[0]
    assert all(f'id="{key}"' in section for key in keys)


def test_the_delivery_tables_hold_the_rows_of_rows_py_once_per_granularity(
    delivery_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = without_values(html_document(delivery_report, 'auto'))
    section = document.split('id="tab-delivery"')[1].split('</section>')[0]
    for title in ('Delivery by period', 'DORA proxies by period'):
        assert section.count(f'<caption>{title}') == 4, title
    assert section.count(' hidden') == 6  # all but the initial granularity of two tables
    assert (
        '<td>2026-10</td><td class=num>7</td><td class=num>80.0%</td>'
        '<td class=num>6.0</td><td class=num>10.8</td><td class=num>4</td>'
    ) in section
    assert '<td>Total</td><td class=num>13</td>' in section
    assert 'minutes and days; - no data' in section
    assert 'proxies: see the README; hours; - no data' in section
    assert 'class="proxies"' in section


def test_a_page_with_delivery_but_no_proxy_has_no_proxy_table_or_line(
    delivery_report: wambatic.reports.html.HtmlReport,
) -> None:
    plain = only_delivery(
        delivery_report,
        lambda metric: (
            not metric.startswith(('deployments', 'lead_time', 'change_failure', 'time_to_restore'))
        ),
    )
    document = html_document(plain, 'auto')
    assert 'Delivery by period' in document
    assert 'DORA proxies by period' not in document
    assert 'class="proxies"' not in document
    assert 'Deployments' not in Page(document).tiles


def popularity_section(document: str) -> str:
    return document.split('id="tab-popularity"')[1].split('</section>')[0]


def test_the_popularity_section_and_tiles_appear_only_with_popularity_series(
    org_report: wambatic.reports.html.HtmlReport,
    popularity_report: wambatic.reports.html.HtmlReport,
) -> None:
    without = html_document(org_report, 'auto')
    assert 'id="tab-popularity"' not in without
    assert 'Top language' not in Page(without).tiles
    page = Page(html_document(popularity_report, 'auto'))
    assert page.by_id('tab-popularity')
    assert page.tiles['Stars'] == '10'  # alpha 6 and beta 4
    assert page.tiles['Forks'] == '5'
    assert page.tiles['Watchers'] == '6'
    assert page.tiles['Top language'] == 'Python'
    assert page.tiles['Commits'] == '10'


def test_the_popularity_section_holds_its_charts_and_says_what_the_counts_are(
    popularity_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(popularity_report, 'auto')
    page = Page(document)
    section = popularity_section(document)
    for key in (
        'popularity-stars-added',
        'popularity-stars-total',
        'popularity-forks-added',
        'popularity-forks-total',
        'popularity-languages',
    ):
        assert page.by_id(key)['role'] == 'img'
        assert f'id="{key}"' in section
    assert 'as of the last sync' in section
    assert 'exist now' in section
    assert (
        'id="popularity-languages"'
        not in document.split('id="tab-commits"')[1].split('</section>')[0]
    )


def test_the_popularity_tables_hold_the_rows_of_rows_py(
    popularity_report: wambatic.reports.html.HtmlReport,
) -> None:
    section = without_values(popularity_section(html_document(popularity_report, 'auto')))
    assert section.count('<caption>Popularity by period') == 4
    assert section.count(' hidden') == 3
    assert '<td>2026-10</td><td class=num>3</td><td class=num>5</td>' in section
    assert (
        '<td>octo-org/alpha</td><td class=num>6</td><td class=num>3</td><td class=num>4</td>'
        in section
    )
    assert '<td>Total</td><td class=num>10</td><td class=num>5</td><td class=num>6</td>' in section
    assert section.count('<tr><td>') >= 4
    assert '<td>Other</td><td class=num>500</td><td class=num>3.4%</td>' in section
    assert 'forks: whole network' in section


def test_a_directory_that_cannot_be_made_is_an_output_error(
    org_report: wambatic.reports.html.HtmlReport, tmp_path: pathlib.Path
) -> None:
    blocker = tmp_path / 'blocker'
    blocker.write_text('a file, not a directory')
    out = blocker / 'report.html'
    folder = out.parent / wambatic.reports.assets.assets_folder_name()
    with pytest.raises(wambatic.reports.errors.OutputError, match=f'cannot write {folder}') as info:
        wambatic.reports.html.render_html(org_report, out, 'auto')
    assert isinstance(info.value.__cause__, OSError)


@pytest.mark.parametrize(
    'error',
    [OSError('gone'), UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte')],
    ids=['os', 'decode'],
)
def test_a_template_that_cannot_be_read_is_an_output_error(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def read_text(self: object, encoding: str | None = None) -> str:
        raise error

    monkeypatch.setattr(pathlib.Path, 'read_text', read_text)
    with pytest.raises(wambatic.reports.errors.OutputError, match='report template report.css'):
        wambatic.reports.assets.read_template('report.css')


def test_a_plotlyjs_that_cannot_be_read_is_an_output_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def get_plotlyjs() -> str:
        raise OSError('gone')

    monkeypatch.setattr(plotly.offline, 'get_plotlyjs', get_plotlyjs)
    with pytest.raises(wambatic.reports.errors.OutputError, match='plotly.js'):
        wambatic.reports.assets.read_plotlyjs()


def test_a_failed_folder_write_leaves_no_page(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(source: object, destination: object) -> None:
        raise OSError(28, 'no space left')

    monkeypatch.setattr(os, 'rename', refuse)
    out = tmp_path / 'out' / 'report.html'
    with pytest.raises(wambatic.reports.errors.OutputError, match='cannot write .*no space left'):
        wambatic.reports.html.render_html(org_report, out, 'auto')
    assert list((tmp_path / 'out').iterdir()) == []


NUMERIC_CELL = re.compile(r'<td class=num data-value="([^"]*)">([^<]*)</td>')
TABLE_HEAD = re.compile(r'<table[^>]*>.*?<thead><tr>(.*?)</tr></thead>', re.DOTALL)
REPORT_FIXTURES = ['delivery_report', 'org_report', 'popularity_report', 'repo_report']


def shown_forms(value: float) -> set[str]:
    format_number = wambatic.reports.terminal.format_number
    return {
        format_number(value),
        format_number(value, signed=True),
        format_number(value, decimals=1),
        f'{value:,.1f}%',
    }


@pytest.mark.parametrize('fixture', REPORT_FIXTURES)
def test_every_numeric_cell_holds_the_value_its_text_was_formatted_from(
    fixture: str, request: pytest.FixtureRequest
) -> None:
    document = html_document(request.getfixturevalue(fixture))
    cells = NUMERIC_CELL.findall(document)
    assert cells
    for raw, text in cells:
        if text == '-':
            assert raw == ''
        else:
            assert html.unescape(text) in shown_forms(float(raw)), (raw, text)


@pytest.mark.parametrize('fixture', REPORT_FIXTURES)
def test_every_header_cell_says_its_type_and_the_first_column_is_text(
    fixture: str, request: pytest.FixtureRequest
) -> None:
    document = html_document(request.getfixturevalue(fixture))
    heads = TABLE_HEAD.findall(document)
    assert heads
    for head in heads:
        kinds = re.findall(r'<th[^>]*data-type="(number|text)"', head)
        assert kinds
        assert kinds[0] == 'text'
        assert head.count('<th') == len(kinds)


@pytest.mark.parametrize(
    ('content', 'expected'),
    [
        (
            wambatic.reports.html.Number('1,234', 1234.0),
            '<td class=num data-value="1234">1,234</td>',
        ),
        (wambatic.reports.html.Number('+56', 56), '<td class=num data-value="56">+56</td>'),
        (
            wambatic.reports.html.Number('12.5%', 12.5),
            '<td class=num data-value="12.5">12.5%</td>',
        ),
        (wambatic.reports.html.Number('-', None), '<td class=num data-value="">-</td>'),
        ('octo', '<td>octo</td>'),
    ],
)
def test_a_cell_carries_the_number_its_text_shows(
    content: str | wambatic.reports.html.Number, expected: str
) -> None:
    assert wambatic.reports.html.cell(content, numeric=False) == expected


def test_the_unavailable_table_has_only_text_columns(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    rows = [{'metric': 'commit dates: octo-org/alpha', 'reason': 'dated in UTC: no author offset'}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'unavailable': rows}
    )
    document = html_document(dataclasses.replace(org_report, total=total))
    section = document.split('id="unavailable"')[1].split('</section>')[0]
    assert section.count('data-type="text"') == 2
    assert 'data-type="number"' not in section
    assert 'data-value' not in section


ACTIVITY_PANELS = ['tab-commits', 'tab-contributors', 'tab-lines']


def panel_ids(document: str) -> list[str]:
    return re.findall(r'<section id="(tab-[a-z]+)" role="tabpanel"', document)


def test_the_panels_follow_the_spec_order_and_hold_their_charts(
    org_report: wambatic.reports.html.HtmlReport,
    delivery_report: wambatic.reports.html.HtmlReport,
    popularity_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(org_report, 'auto')
    assert panel_ids(document)[:3] == ACTIVITY_PANELS
    commits = document.split('id="tab-commits"')[1].split('</section>')[0]
    assert 'id="activity-commits"' in commits
    assert 'id="activity-active-days"' in commits
    assert 'id="activity-calendar"' in commits
    assert 'id="activity-lines"' not in commits
    contributors = document.split('id="tab-contributors"')[1].split('</section>')[0]
    assert 'id="activity-contributors"' in contributors
    assert 'id="activity-top-contributors"' in contributors
    assert 'id="activity-commits"' not in contributors
    lines = document.split('id="tab-lines"')[1].split('</section>')[0]
    assert 'id="activity-lines"' in lines
    assert panel_ids(html_document(delivery_report, 'auto')) == [
        'tab-commits',
        'tab-contributors',
        'tab-lines',
        'tab-flow',
        'tab-delivery',
    ]
    assert panel_ids(html_document(popularity_report, 'auto'))[-1] == 'tab-popularity'


def test_every_tab_button_names_its_panel_and_the_bar_is_hidden_until_script_runs(
    popularity_report: wambatic.reports.html.HtmlReport,
) -> None:
    document = html_document(popularity_report, 'auto')
    ids = panel_ids(document)
    assert '<div class="tab-bar" role="tablist" hidden>' in document
    assert re.findall(r'role="tab" id="[a-z-]+" aria-controls="(tab-[a-z]+)"', document) == ids
    panels = re.findall(r'<section id="tab-[^>]*>', document)
    assert panels and all('hidden' not in tag for tag in panels)


def test_unavailable_sits_outside_the_panels(
    org_report: wambatic.reports.html.HtmlReport,
) -> None:
    rows = [{'metric': 'releases', 'reason': 'not fetched'}]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'unavailable': rows}
    )
    report = dataclasses.replace(org_report, total=total)
    document = html_document(report, 'auto')
    before = document.split('<section id="unavailable">')[0]
    assert before.count('<section') == before.count('</section>')
    assert document.rindex('role="tabpanel"') < document.index('id="unavailable"')
