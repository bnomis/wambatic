import importlib

import pytest

import wambatic
import wambatic.cli
import wambatic.fetch
import wambatic.fetch.base
import wambatic.reports
import wambatic.reports.service
import wambatic.stats
import wambatic.stats.base
import wambatic.stats.engine


@pytest.mark.parametrize(
    'name', ['wambatic', 'wambatic.cli', 'wambatic.fetch', 'wambatic.reports', 'wambatic.stats']
)
def test_package_imports(name: str) -> None:
    assert importlib.import_module(name).__name__ == name


def test_the_public_surface_is_what_the_system_spec_lists() -> None:
    assert sorted(wambatic.__all__) == [
        'Fetcher',
        'Settings',
        'StatsRequest',
        'StatsResult',
        'Subject',
        'compute',
        'load_settings',
    ]


@pytest.mark.parametrize('name', wambatic.__all__)
def test_public_names_resolve(name: str) -> None:
    assert getattr(wambatic, name)


@pytest.mark.parametrize('package', [wambatic.fetch, wambatic.reports, wambatic.stats])
def test_subpackages_export_nothing(package: object) -> None:
    assert not hasattr(package, '__all__')


def test_the_top_level_names_are_the_submodules_objects() -> None:
    assert wambatic.Fetcher is wambatic.fetch.base.Fetcher
    assert wambatic.Subject is wambatic.fetch.base.Subject
    assert wambatic.compute is wambatic.stats.engine.compute
    assert wambatic.StatsRequest is wambatic.stats.base.StatsRequest
    assert wambatic.StatsResult is wambatic.stats.base.StatsResult


def test_the_service_names_are_in_the_service_module() -> None:
    assert hasattr(wambatic.reports.service, 'parse_target')


def test_the_command_line_entry_points_are_callable() -> None:
    assert callable(wambatic.cli.main)
    assert callable(wambatic.cli.run)


def test_popularity_is_a_group() -> None:
    assert 'popularity' in wambatic.stats.base.GROUPS
