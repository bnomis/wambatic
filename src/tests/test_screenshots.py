"""Tests for bin/screenshots.py. No test uses the network."""

import datetime
import importlib.util
import pathlib
import re
import types

import pytest
import rich.console

import tests.conftest
import tests.fixtures.stats
import wambatic.fetch.base
import wambatic.fetch.errors
import wambatic.reports.html
import wambatic.reports.terminal
import wambatic.settings
import wambatic.version

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / 'bin/screenshots.py'


def load_script() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location('screenshots_script', SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screenshots = load_script()


def render_two_headings(console: rich.console.Console) -> None:
    console.print('titleline')
    wambatic.reports.terminal.heading(console, 'Trends')
    console.print('trendrows')
    wambatic.reports.terminal.heading(console, 'By repository')
    console.print('repositoryrows')


def test_split_sections_cuts_at_each_heading() -> None:
    sections = screenshots.split_sections(render_two_headings)
    assert list(sections) == ['overview', 'trends', 'by-repository']
    assert 'titleline' in sections['overview']
    assert 'trendrows' in sections['trends']
    assert 'repositoryrows' not in sections['trends']
    assert 'repositoryrows' in sections['by-repository']
    assert 'Trends' not in sections['overview']


def test_split_sections_restores_the_heading_function() -> None:
    before = wambatic.reports.terminal.heading
    screenshots.split_sections(render_two_headings)
    assert wambatic.reports.terminal.heading is before


def test_split_sections_restores_the_heading_function_after_a_failure() -> None:
    before = wambatic.reports.terminal.heading

    def failing(_: rich.console.Console) -> None:
        raise RuntimeError('render failed')

    with pytest.raises(RuntimeError):
        screenshots.split_sections(failing)
    assert wambatic.reports.terminal.heading is before


def test_split_sections_names_a_repeated_heading_once_each() -> None:
    def render(console: rich.console.Console) -> None:
        wambatic.reports.terminal.heading(console, 'Flow')
        wambatic.reports.terminal.heading(console, 'Flow')

    assert list(screenshots.split_sections(render)) == ['overview', 'flow', 'flow-2']


def test_a_file_over_one_megabyte_is_refused(tmp_path: pathlib.Path) -> None:
    big = tmp_path / 'big.png'
    big.write_bytes(b'x' * (screenshots.MAX_BYTES + 1))
    with pytest.raises(screenshots.ScreenshotError, match=re.escape(str(big))):
        screenshots.check_size(big)
    small = tmp_path / 'small.png'
    small.write_bytes(b'x' * screenshots.MAX_BYTES)
    assert screenshots.check_size(small) == small


def test_a_missing_token_names_the_fix(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse() -> str:
        raise wambatic.fetch.errors.AuthError(wambatic.fetch.errors.NO_TOKEN_MESSAGE)

    monkeypatch.setattr(screenshots.wambatic.fetch.auth, 'fetch_token', refuse)
    with pytest.raises(screenshots.ScreenshotError, match='GITHUB_TOKEN'):
        screenshots.check_token()


def test_main_reports_a_missing_token_on_one_line_and_exits_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    def refuse() -> str:
        raise wambatic.fetch.errors.AuthError(wambatic.fetch.errors.NO_TOKEN_MESSAGE)

    monkeypatch.setattr(screenshots.wambatic.fetch.auth, 'fetch_token', refuse)
    assert screenshots.main(['--out', str(tmp_path / 'images')]) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert len(captured.err.splitlines()) == 1
    assert 'GITHUB_TOKEN' in captured.err
    assert not (tmp_path / 'images').exists()


def test_the_config_names_the_docs_cache_and_utc(tmp_path: pathlib.Path) -> None:
    config = screenshots.write_config(tmp_path, tmp_path / 'docs.sqlite3')
    with screenshots.config_environment(config):
        settings = wambatic.settings.load_settings(None, {})
    assert settings.fetch.cache_path == tmp_path / 'docs.sqlite3'
    assert settings.stats.timezone == 'UTC'


def test_the_docs_cache_is_never_the_users_own() -> None:
    assert screenshots.DOCS_CACHE != wambatic.settings.cache_path_for(
        wambatic.settings.FetchSettings()
    )


def test_wanted_images_are_those_the_guide_references() -> None:
    docs = SCRIPT.parent.parent / 'docs'
    images = (docs / 'images').resolve()
    link = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')
    referenced = set()
    for page in docs.rglob('*.md'):
        for target in link.findall(page.read_text(encoding='utf-8')):
            if '://' not in target:
                image = (page.parent / target).resolve()
                if image.is_relative_to(images):
                    referenced.add(image.relative_to(images).as_posix())
    assert referenced == screenshots.WANTED


def test_only_wanted_images_are_selected(tmp_path: pathlib.Path) -> None:
    assert screenshots.is_wanted(tmp_path, tmp_path / 'web/form.png')
    assert not screenshots.is_wanted(tmp_path, tmp_path / 'web/unused.png')


def test_the_captured_note_names_the_date_and_version() -> None:

    note = screenshots.captured_note(datetime.date(2026, 11, 1))
    assert '2026-11-01' in note
    assert wambatic.version.VERSION in note
    assert screenshots.SINCE in note
    assert screenshots.UNTIL in note


@pytest.mark.browser
def test_every_selector_matches_an_html_report(
    stats_fetcher: wambatic.fetch.base.Fetcher,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    every_image = {f'html/org-octo-org-{crop.name}.png' for crop in screenshots.SELECTORS} | {
        'html/org-octo-org-light.png',
        'html/org-octo-org-dark.png',
    }
    monkeypatch.setattr(screenshots, 'WANTED', frozenset(every_image))
    report = tests.conftest.make_report(
        stats_fetcher,
        tests.fixtures.stats.ORG,
        by_author=True,
        groups=tests.fixtures.stats.GROUPS_ALL,
    )
    path = wambatic.reports.html.render_html(report, tmp_path / 'report-org-octo-org.html', 'auto')
    try:
        written = screenshots.capture_html(path, tmp_path / 'images')
    except screenshots.ScreenshotError as e:
        if 'Chromium cannot be launched' in str(e):
            pytest.skip(str(e))
        raise
    names = {item.name for item in written}
    for crop in screenshots.SELECTORS:
        assert f'org-octo-org-{crop.name}.png' in names
    assert {'org-octo-org-light.png', 'org-octo-org-dark.png'} <= names


@pytest.mark.browser
def test_a_selector_that_matches_nothing_is_named(
    stats_fetcher: wambatic.fetch.base.Fetcher, tmp_path: pathlib.Path
) -> None:
    report = tests.conftest.make_report(stats_fetcher, tests.fixtures.stats.ORG)
    path = wambatic.reports.html.render_html(report, tmp_path / 'report.html', 'auto')
    crop = screenshots.Crop('missing', '#no-such-element')
    try:
        with screenshots.launch_chromium() as browser:
            with pytest.raises(screenshots.ScreenshotError, match='#no-such-element'):
                screenshots.crop_report(browser, path, crop, tmp_path / 'out.png')
    except screenshots.ScreenshotError as e:
        if 'Chromium cannot be launched' in str(e):
            pytest.skip(str(e))
        raise
