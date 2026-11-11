import collections.abc
import dataclasses
import pathlib
import typing

import openpyxl
import playwright.sync_api
import pytest

import tests.fixtures.reports
import tests.reports.conftest
import wambatic.reports.assets
import wambatic.reports.figures
import wambatic.reports.html
import wambatic.settings
import wambatic.stats.base

pytestmark = pytest.mark.browser

FIRST_CHART = 'activity-commits'
DARK_SURFACE = wambatic.reports.figures.PALETTE['dark'].surface
LIGHT_SURFACE = wambatic.reports.figures.PALETTE['light'].surface


@dataclasses.dataclass
class Opened:
    page: playwright.sync_api.Page
    requests: list[str]
    problems: list[str]


@pytest.fixture
def open_report(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> collections.abc.Iterator[collections.abc.Callable[..., Opened]]:
    contexts: list[playwright.sync_api.BrowserContext] = []

    def open_page(
        theme: wambatic.settings.Theme = 'auto',
        scheme: typing.Literal['dark', 'light'] = 'light',
        report: wambatic.reports.html.HtmlReport = org_report,
    ) -> Opened:
        out = wambatic.reports.html.render_html(report, tmp_path / 'out' / 'report.html', theme)
        context = chromium.new_context(color_scheme=scheme)
        contexts.append(context)
        page = context.new_page()
        folder = (out.parent / wambatic.reports.assets.assets_folder_name()).as_uri() + '/'
        requests, problems = tests.reports.conftest.watch_page(
            page, lambda url: url == out.as_uri() or url.startswith(folder)
        )
        page.goto(out.as_uri())
        page.wait_for_selector(f'#{FIRST_CHART} .main-svg')
        return Opened(page, requests, problems)

    yield open_page
    for context in contexts:
        context.close()


def show_chart(page: playwright.sync_api.Page, key: str) -> None:
    """Open the tab holding chart `key` and wait for it to be drawn."""
    panel: str = page.evaluate(f'document.getElementById("{key}").closest("[role=tabpanel]").id')
    page.click(f'[role=tab][aria-controls={panel}]')
    page.wait_for_selector(f'#{key} .main-svg')


def keys(report: wambatic.reports.html.HtmlReport) -> list[str]:
    figures = [
        figure
        for result in report.periods.values()
        for figure in wambatic.reports.figures.build_figures(result)
    ]
    calendar = wambatic.reports.figures.build_calendar(
        report.periods[wambatic.stats.base.Granularity.DAY]
    )
    assert calendar is not None
    figures += wambatic.reports.figures.build_range_figures(report.total) + [calendar]
    return sorted({figure.key for figure in figures})


def test_the_file_opens_offline_without_errors_and_every_chart_is_drawn(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    expected = keys(org_report)
    assert 'activity-calendar' in expected
    for key in expected:
        show_chart(opened.page, key)
        width: float = opened.page.evaluate(
            f'document.getElementById("{key}").getBoundingClientRect().width'
        )
        assert width > 0, key
    assert opened.requests == []
    assert opened.problems == []


def test_a_delivery_report_draws_every_chart_with_no_request_or_error(
    delivery_report: wambatic.reports.html.HtmlReport,
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report(report=delivery_report)
    expected = keys(delivery_report)
    assert {'delivery-runs', 'delivery-lead-time', 'delivery-time-to-restore'} <= set(expected)
    for key in expected:
        show_chart(opened.page, key)
    for granularity in wambatic.reports.html.PERIODS:
        opened.page.check(f'input[name=granularity][value={granularity}]')
        show_chart(opened.page, 'delivery-runs')
    assert opened.requests == []
    assert opened.problems == []


def test_a_popularity_report_draws_every_chart_with_no_request_or_error(
    popularity_report: wambatic.reports.html.HtmlReport,
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report(report=popularity_report)
    expected = keys(popularity_report)
    assert {'popularity-stars-added', 'popularity-languages'} <= set(expected)
    for key in expected:
        show_chart(opened.page, key)
    for granularity in wambatic.reports.html.PERIODS:
        opened.page.check(f'input[name=granularity][value={granularity}]')
        show_chart(opened.page, 'popularity-stars-total')
    assert opened.requests == []
    assert opened.problems == []


def visible_tables(page: playwright.sync_api.Page) -> set[str]:
    found = page.eval_on_selector_all(
        'table.period',
        'tables => tables.filter(t => !t.hidden).map(t => t.dataset.granularity)',
    )
    return set(found)


def test_each_granularity_shows_its_own_buckets_and_tables(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    page = opened.page
    assert visible_tables(page) == tests.fixtures.reports.MONTH_ONLY
    for granularity in wambatic.reports.html.PERIODS:
        figures = wambatic.reports.figures.build_figures(org_report.periods[granularity])
        expected = len(figures[0].data[0]['x'])  # type: ignore[arg-type]
        page.check(f'input[name=granularity][value={granularity}]')
        page.wait_for_function(
            f'document.getElementById("{FIRST_CHART}").data[0].x.length === {expected}'
        )
        assert visible_tables(page) == {str(granularity)}
    assert opened.requests == []
    assert opened.problems == []


def surface(page: playwright.sync_api.Page) -> str:
    colour: str = page.evaluate(
        f'document.getElementById("{FIRST_CHART}")._fullLayout.paper_bgcolor'
    )
    return colour


def test_auto_follows_the_system_scheme_and_a_change_of_it(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    dark = open_report('auto', 'dark')
    assert surface(dark.page) == DARK_SURFACE
    dark.page.emulate_media(color_scheme='light')
    dark.page.wait_for_function(
        f'document.getElementById("{FIRST_CHART}")._fullLayout.paper_bgcolor === "{LIGHT_SURFACE}"'
    )
    light = open_report('auto', 'light')
    assert surface(light.page) == LIGHT_SURFACE
    assert dark.problems == [] and light.problems == []


def test_a_fixed_theme_ignores_the_system_scheme(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report('light', 'dark')
    assert surface(opened.page) == LIGHT_SURFACE
    opened.page.emulate_media(color_scheme='dark')
    opened.page.wait_for_timeout(300)
    assert surface(opened.page) == LIGHT_SURFACE
    fixed_dark = open_report('dark', 'light')
    assert surface(fixed_dark.page) == DARK_SURFACE


def test_the_series_take_the_themes_colours(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report('auto', 'dark')
    colour: str = opened.page.evaluate(
        f'document.getElementById("{FIRST_CHART}").data[0].marker.color'
    )
    assert colour == wambatic.reports.figures.PALETTE['dark'].categorical[0]


def test_a_page_opened_without_its_folder_shows_the_missing_files_notice(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    lonely = tmp_path / 'copy' / 'report.html'
    lonely.parent.mkdir()
    lonely.write_bytes(out.read_bytes())
    context = chromium.new_context()
    try:
        page = context.new_page()
        page.goto(lonely.as_uri())
        notice = page.locator('.assets-missing')
        notice.wait_for(state='visible')
        folder = wambatic.reports.assets.assets_folder_name()
        assert notice.inner_text() == (
            f"This report's files ({folder}) did not load; keep the page beside that folder."
        )
        assert page.locator('table:not([hidden])').first.is_visible()
    finally:
        context.close()


def test_a_page_opened_with_its_folder_hides_the_missing_files_notice(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report()
    assert not opened.page.locator('.assets-missing').is_visible()


def selected_tab(page: playwright.sync_api.Page) -> str:
    selected: str = page.eval_on_selector(
        '[role=tab][aria-selected=true]', 'button => button.getAttribute("aria-controls")'
    )
    return selected


def test_a_tab_first_opened_after_a_granularity_switch_shows_that_granularity(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    page = opened.page
    page.check('input[name=granularity][value=day]')
    page.click('[role=tab][aria-controls=tab-lines]')
    figures = wambatic.reports.figures.build_figures(
        org_report.periods[wambatic.stats.base.Granularity.DAY]
    )
    lines = next(f for f in figures if f.key == 'activity-lines')
    expected = len(lines.data[0]['x'])  # type: ignore[arg-type]
    page.wait_for_function(
        f'document.getElementById("activity-lines").data[0].x.length === {expected}'
    )
    assert opened.problems == []


def test_the_first_tab_shows_on_load_and_the_arrow_keys_home_and_end_move_the_selection(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report()
    page = opened.page
    tabs = page.eval_on_selector_all(
        '[role=tab]', 'buttons => buttons.map(b => b.getAttribute("aria-controls"))'
    )
    assert tabs[0] == 'tab-commits' and len(tabs) >= 4
    assert selected_tab(page) == tabs[0]
    shown = page.eval_on_selector_all(
        '[role=tabpanel]', 'panels => panels.filter(p => !p.hidden).map(p => p.id)'
    )
    assert shown == [tabs[0]]
    page.focus(f'[role=tab][aria-controls={tabs[0]}]')
    page.keyboard.press('ArrowRight')
    assert selected_tab(page) == tabs[1]
    page.keyboard.press('End')
    assert selected_tab(page) == tabs[-1]
    page.keyboard.press('ArrowRight')
    assert selected_tab(page) == tabs[0]
    page.keyboard.press('ArrowLeft')
    assert selected_tab(page) == tabs[-1]
    page.keyboard.press('Home')
    assert selected_tab(page) == tabs[0]
    assert page.url.endswith('#tab-commits')
    assert opened.problems == []


def test_a_fragment_opens_on_its_tab(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    context = chromium.new_context()
    try:
        page = context.new_page()
        page.goto(f'{out.as_uri()}#tab-flow')
        page.wait_for_selector('#tab-flow:not([hidden])')
        assert selected_tab(page) == 'tab-flow'
    finally:
        context.close()


def test_with_script_disabled_every_panel_shows(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    context = chromium.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(out.as_uri())
        panels = page.locator('[role=tabpanel]')
        assert panels.count() >= 4
        for index in range(panels.count()):
            assert panels.nth(index).is_visible()
        assert not page.locator('[role=tablist]').is_visible()
    finally:
        context.close()


# auditme: accept[non-alphabetical-literal] the order a case-blind, number-aware sort gives
LOGINS_BY_NAME = ['alpha', 'Beta', 'gamma2', 'gamma10']
PLANTED = (
    ('alpha', 5, 100),
    ('Beta', 12, 40),
    ('gamma10', 1, 2500),
    ('gamma2', 7, 0),
)


@pytest.fixture
def contributors(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> tuple[Opened, playwright.sync_api.Locator]:
    rows = [
        {
            'login': login,
            'commits': commits,
            'lines_added': added,
            'lines_deleted': 0,
            'lines_net': added,
            'active_days': 1,
        }
        for login, commits, added in PLANTED
    ]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'top_contributors': rows}
    )
    opened = open_report(report=dataclasses.replace(org_report, total=total))
    opened.page.click('[role=tab][aria-controls=tab-contributors]')
    table = table_titled(opened.page, 'Top contributors')
    return opened, table


def table_titled(page: playwright.sync_api.Page, title: str) -> playwright.sync_api.Locator:
    """The visible table whose caption starts with `title`, with its block opened."""
    table = page.locator('table:not([hidden])', has=page.locator('caption', has_text=title)).first
    table.evaluate('table => { table.closest("details").open = true }')
    return table


def column(table: playwright.sync_api.Locator, index: int) -> list[str]:
    visible = 'tbody tr:not([hidden])'
    cells: list[str] = table.locator(
        f'{visible} td:nth-child({index}), {visible} th:nth-child({index})'
    ).all_inner_texts()
    return cells


def number_of(text: str) -> int:
    return int(text.replace(',', ''))


def sort_by(table: playwright.sync_api.Locator, name: str) -> None:
    table.locator('thead tr:first-child th', has_text=name).locator('button.sort').click()


def test_sorting_orders_numbers_by_value_with_empty_values_last_both_ways(
    contributors: tuple[Opened, playwright.sync_api.Locator],
) -> None:
    opened, table = contributors
    table.locator('tbody tr:nth-child(2) td:nth-child(3)').evaluate(
        'cell => { cell.setAttribute("data-value", ""); cell.textContent = "-" }'
    )
    original = column(table, 1)
    header = table.locator('thead tr:first-child th', has_text='Added')
    sort_by(table, 'Added')
    ascending = column(table, 3)
    assert ascending[-1] == '-'
    values = [number_of(v) for v in ascending[:-1]]
    assert values == sorted(values)
    assert header.get_attribute('aria-sort') == 'ascending'
    sort_by(table, 'Added')
    descending = column(table, 3)
    assert descending[-1] == '-'
    values = [number_of(v) for v in descending[:-1]]
    assert values == sorted(values, reverse=True)
    assert header.get_attribute('aria-sort') == 'descending'
    sort_by(table, 'Added')
    assert column(table, 1) == original
    assert header.get_attribute('aria-sort') == 'none'
    assert opened.problems == []


def test_sorting_text_compares_numbers_inside_the_text_by_value(
    contributors: tuple[Opened, playwright.sync_api.Locator],
) -> None:
    _, table = contributors
    sort_by(table, 'Login')
    assert column(table, 1) == LOGINS_BY_NAME


def status_line(table: playwright.sync_api.Locator) -> playwright.sync_api.Locator:
    return table.locator('xpath=following-sibling::p[@role="status"]')


def wait_for_rows(table: playwright.sync_api.Locator, logins: list[str]) -> None:
    expected = f'Showing {len(logins)} of {len(PLANTED)} rows'
    for _ in range(40):
        if status_line(table).inner_text() == expected and sorted(column(table, 1)) == sorted(
            logins
        ):
            break
        table.page.wait_for_timeout(50)
    assert status_line(table).inner_text() == expected
    assert sorted(column(table, 1)) == sorted(logins)


def test_a_text_filter_ignores_case_and_a_number_filter_takes_each_form(
    contributors: tuple[Opened, playwright.sync_api.Locator],
) -> None:
    _, table = contributors
    boxes = table.locator('tr.filters input')
    boxes.nth(0).fill('GAMMA')
    wait_for_rows(table, ['gamma10', 'gamma2'])
    boxes.nth(0).fill('')
    cases: dict[str, collections.abc.Callable[[int], bool]] = {
        '5': lambda commits: commits == 5,
        '=5': lambda commits: commits == 5,
        '>5': lambda commits: commits > 5,
        '>=5': lambda commits: commits >= 5,
        '<5': lambda commits: commits < 5,
        '<=5': lambda commits: commits <= 5,
        '5..7': lambda commits: 5 <= commits <= 7,
    }
    for text, keep in cases.items():
        boxes.nth(1).fill(text)
        wait_for_rows(table, [login for login, commits, _ in PLANTED if keep(commits)])
    boxes.nth(1).fill('')
    boxes.nth(2).fill('>=1,000')
    wait_for_rows(table, [login for login, _, added in PLANTED if added >= 1000])
    boxes.nth(1).fill('>5')
    wait_for_rows(table, [])


def test_an_unreadable_filter_is_marked_and_filters_nothing(
    contributors: tuple[Opened, playwright.sync_api.Locator],
) -> None:
    _, table = contributors
    boxes = table.locator('tr.filters input')
    boxes.nth(1).fill('lots')
    table.locator('tr.filters input[aria-invalid="true"]').wait_for()
    wait_for_rows(table, [login for login, _, _ in PLANTED])
    boxes.nth(1).fill('>5')
    wait_for_rows(table, [login for login, commits, _ in PLANTED if commits > 5])
    assert boxes.nth(1).get_attribute('aria-invalid') is None


def test_the_total_row_keeps_its_place_and_is_relabelled_while_a_filter_is_on(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    page = open_report().page
    table = table_titled(page, 'Activity by period')
    label = table.locator('tfoot td').first
    assert label.inner_text() == 'Total'
    sort_by(table, 'Commits')
    sort_by(table, 'Commits')
    assert table.locator('tbody + tfoot').count() == 1
    table.locator('tr.filters input').first.fill('zzz-no-such-period')
    page.wait_for_function(
        'text => document.querySelector("table:not([hidden]) tfoot td").textContent === text',
        arg='Total (all rows)',
    )
    assert column(table, 1) == []
    table.locator('tr.filters input').first.fill('')
    page.wait_for_function(
        'text => document.querySelector("table:not([hidden]) tfoot td").textContent === text',
        arg='Total',
    )


def test_the_summary_count_follows_a_granularity_switch(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    page = open_report().page
    block = page.locator('details.table-block', has=page.locator('table.period')).first
    for granularity in ('day', 'year'):
        page.check(f'input[name=granularity][value={granularity}]')
        expected = block.locator(f'table.period[data-granularity={granularity}] tbody tr').count()
        assert expected > 0
        assert block.locator('.row-count').inner_text() == (
            f'{expected} row' if expected == 1 else f'{expected} rows'
        )


EXPORTED = (*PLANTED, ('=cmd', 3, 10))


@pytest.fixture
def exporting(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> tuple[Opened, playwright.sync_api.Locator]:
    rows = [
        {
            'login': login,
            'commits': commits,
            'lines_added': added,
            'lines_deleted': 0,
            'lines_net': added,
            'active_days': 1,
        }
        for login, commits, added in EXPORTED
    ]
    total = dataclasses.replace(
        org_report.total, tables={**org_report.total.tables, 'top_contributors': rows}
    )
    opened = open_report(report=dataclasses.replace(org_report, total=total))
    opened.page.click('[role=tab][aria-controls=tab-contributors]')
    return opened, table_titled(opened.page, 'Top contributors')


def download_of(
    table: playwright.sync_api.Locator, button: str, tmp_path: pathlib.Path
) -> pathlib.Path:
    with table.page.expect_download() as info:
        table.locator('xpath=following-sibling::div[@class="table-tools"]').get_by_role(
            'button', name=button, exact=True
        ).click()
    target = tmp_path / info.value.suggested_filename
    info.value.save_as(target)
    return target


def wait_for_logins(table: playwright.sync_api.Locator, expected: list[str]) -> None:
    for _ in range(40):
        if column(table, 1) == expected:
            break
        table.page.wait_for_timeout(50)
    assert column(table, 1) == expected


def test_csv_holds_the_shown_rows_in_the_shown_order_and_guards_formulas(
    exporting: tuple[Opened, playwright.sync_api.Locator], tmp_path: pathlib.Path
) -> None:
    _, table = exporting
    table.locator('tr.filters input').nth(1).fill('>1')
    sort_by(table, 'Commits')
    sort_by(table, 'Commits')
    expected = [
        login for login, commits, _ in sorted(EXPORTED, key=lambda row: -row[1]) if commits > 1
    ]
    wait_for_logins(table, expected)
    target = download_of(table, 'CSV', tmp_path)
    assert target.name.endswith('-top-contributors.csv')
    raw = target.read_bytes()
    assert raw.startswith(b'\xef\xbb\xbf')
    lines = raw.decode('utf-8-sig').split('\r\n')
    assert lines[-1] == ''
    assert lines[0].split(',')[0] == 'Login'
    assert [line.split(',')[0] for line in lines[1:-1]] == [
        "'" + login if login == '=cmd' else login for login in expected
    ]
    assert lines[1].split(',')[1] == '12'


def test_excel_holds_the_shown_rows_with_numbers_as_numbers(
    exporting: tuple[Opened, playwright.sync_api.Locator], tmp_path: pathlib.Path
) -> None:
    _, table = exporting
    table.locator('tr.filters input').nth(0).fill('a')
    sort_by(table, 'Login')
    expected = LOGINS_BY_NAME
    wait_for_logins(table, expected)
    target = download_of(table, 'Excel', tmp_path)
    assert target.name.endswith('-top-contributors.xlsx')
    sheet = openpyxl.load_workbook(target).active
    assert sheet is not None
    assert sheet.title == 'Top contributors'
    rows = list(sheet.iter_rows(values_only=True))
    assert rows[0][0] == 'Login'
    assert sheet.cell(1, 1).font.bold
    assert [row[0] for row in rows[1:]] == expected
    assert all(isinstance(row[1], int | float) for row in rows[1:])
    assert all(cell.data_type != 'f' for row in sheet.iter_rows() for cell in row)


def test_a_missing_excel_library_shows_one_failure_line_and_saves_nothing(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    folder = out.parent / wambatic.reports.assets.assets_folder_name()
    (folder / 'write-excel-file.min.js').unlink()
    context = chromium.new_context()
    try:
        page = context.new_page()
        downloads: list[object] = []
        page.on('download', lambda download: downloads.append(download))
        page.goto(out.as_uri())
        page.wait_for_selector(f'#{FIRST_CHART} .main-svg')
        table = page.locator('table.period:not([hidden])').first
        table.evaluate('table => { table.closest("details").open = true }')
        tools = table.locator('xpath=following-sibling::div[@class="table-tools"]')
        tools.get_by_role('button', name='Excel', exact=True).click()
        playwright.sync_api.expect(tools.locator('.export-error')).to_have_text(
            'The export failed; nothing was saved.'
        )
        page.wait_for_timeout(200)
        assert downloads == []
    finally:
        context.close()
