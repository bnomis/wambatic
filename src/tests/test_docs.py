import dataclasses
import datetime
import json
import pathlib
import re
import typing

import cappa

import wambatic.cli
import wambatic.settings
import wambatic.stats.activity
import wambatic.stats.base
import wambatic.stats.delivery
import wambatic.stats.flow
import wambatic.stats.popularity

DOCS = pathlib.Path(__file__).resolve().parents[2] / 'docs'
REFERENCE = DOCS / 'reference'
GLOBAL_EXTRAS = frozenset({'--completion', '--help', '-h'})
CODE_SPAN = re.compile(r'`([^`]*)`')
CELL_SPLIT = re.compile(r'(?<!\\)\|')


def split_row(line: str) -> list[str]:
    body = line.strip().removeprefix('|').removesuffix('|')
    return [cell.strip() for cell in CELL_SPLIT.split(body)]


def doc_table(page: pathlib.Path, heading: str) -> list[dict[str, str]]:
    """The rows of the first Markdown table under `heading` in `page`, keyed by column header."""
    lines = page.read_text(encoding='utf-8').splitlines()
    start = next(
        (
            i
            for i, line in enumerate(lines)
            if line.startswith('#') and line.lstrip('#').strip() == heading
        ),
        None,
    )
    if start is None:
        raise AssertionError(f'{page}: no heading {heading!r}')
    table: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith('|'):
            table.append(line)
        elif table or line.startswith('#'):
            break
    if len(table) < 2:
        raise AssertionError(f'{page}: no table under {heading!r}')
    header = split_row(table[0])
    return [dict(zip(header, split_row(row), strict=True)) for row in table[2:]]


def names_in(cell: str) -> list[str]:
    """The first word of each code span in a cell: `--by year|month` gives `--by`."""
    return [span.split(' ')[0] for span in CODE_SPAN.findall(cell)]


def as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else [value]


def class_options(cls: type) -> set[str]:
    hints = typing.get_type_hints(cls, include_extras=True)
    options: set[str] = set()
    for field in dataclasses.fields(cls):
        arg = next(
            (m for m in getattr(hints[field.name], '__metadata__', ()) if isinstance(m, cappa.Arg)),
            None,
        )
        if field.name == 'command':
            continue
        if arg is None or not arg.long:
            options.add(field.name.upper())
            continue
        options.add(f'--{field.name.replace("_", "-")}')
        if arg.short:
            options.update(str(short) for short in as_list(arg.short))
    return options


def check_options(heading: str, cls: type, extras: frozenset[str] = frozenset()) -> None:
    rows = doc_table(REFERENCE / 'cli.md', heading)
    documented = {name for row in rows for name in names_in(row['Option'])} - extras
    expected = class_options(cls)
    assert documented == expected, (
        f'reference/cli.md, {heading}: missing {sorted(expected - documented)}, '
        f'unexpected {sorted(documented - expected)}'
    )


def test_cli_options_match() -> None:
    check_options('Global options', wambatic.cli.Wambatic, GLOBAL_EXTRAS)
    check_options('report', wambatic.cli.Report)
    check_options('serve', wambatic.cli.Serve)
    check_options('cache', wambatic.cli.CacheCommand)


def parse_default(text: str, annotation: object) -> object:
    value = text.strip().strip('`')
    if value == 'none':
        return None
    if annotation is datetime.timedelta:
        return wambatic.settings.parse_duration(value)
    if annotation is pathlib.Path:
        return pathlib.Path(value).expanduser()
    if annotation == tuple[str, ...]:
        return tuple(json.loads(value))
    if annotation is bool:
        return json.loads(value)
    if annotation is int:
        return int(value)
    return value


def test_settings_match() -> None:
    rows = doc_table(REFERENCE / 'settings.md', 'Settings table')
    documented = {names_in(row['Setting'])[0]: row for row in rows}
    expected: dict[str, tuple[object, object]] = {}
    for section, cls in wambatic.settings.SECTIONS.items():
        hints = typing.get_type_hints(cls)
        defaults = cls()
        for field in dataclasses.fields(cls):
            expected[f'{section}.{field.name}'] = (hints[field.name], getattr(defaults, field.name))
    assert set(documented) == set(expected), (
        f'reference/settings.md: missing {sorted(set(expected) - set(documented))}, '
        f'unexpected {sorted(set(documented) - set(expected))}'
    )
    for key, (annotation, default) in expected.items():
        actual = parse_default(documented[key]['Default'], annotation)
        assert actual == default, (
            f'reference/settings.md, {key}: documented default {actual!r}, code {default!r}'
        )


METRIC_SOURCES: dict[str, tuple[tuple[str, str], ...]] = {
    'activity': wambatic.stats.activity.TOTAL_METRICS,
    'delivery': wambatic.stats.delivery.DELIVERY_METRICS,
    'flow': wambatic.stats.flow.FLOW_METRICS,
    'popularity': wambatic.stats.popularity.POPULARITY_METRICS,
}


def test_metrics_match() -> None:
    rows = doc_table(REFERENCE / 'metrics.md', 'Metrics table')
    documented = {names_in(row['Metric'])[0]: (row['Group'], row['Unit']) for row in rows}
    expected = {
        name: (group, unit) for group, metrics in METRIC_SOURCES.items() for name, unit in metrics
    }
    shared = expected.keys() & documented.keys()
    different = sorted(k for k in shared if expected[k] != documented[k])
    assert documented == expected, (
        f'reference/metrics.md: missing {sorted(set(expected) - set(documented))}, '
        f'unexpected {sorted(set(documented) - set(expected))}, different {different}'
    )


def test_groups_match() -> None:
    rows = doc_table(REFERENCE / 'metrics.md', 'Groups')
    documented = {names_in(row['Group'])[0] for row in rows}
    assert documented == set(wambatic.stats.base.GROUPS)


IMAGE_LINK = re.compile(r'!\[[^\]]*\]\(([^)\s]+)')


def test_images_exist() -> None:
    referenced: set[pathlib.Path] = set()
    for page in DOCS.rglob('*.md'):
        for link in IMAGE_LINK.findall(page.read_text(encoding='utf-8')):
            if '://' in link:
                continue
            image = (page.parent / link).resolve()
            assert image.is_file(), f'{page.relative_to(DOCS)} references {link}, which is missing'
            referenced.add(image)
    on_disk = {path.resolve() for path in (DOCS / 'images').rglob('*') if path.is_file()}
    unreferenced = sorted(str(path.relative_to(DOCS.resolve())) for path in on_disk - referenced)
    assert not unreferenced, f'unreferenced images: {unreferenced}'
