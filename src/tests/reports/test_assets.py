import hashlib
import importlib.resources
import os
import pathlib
import shutil
import stat

import pytest

import wambatic.reports.assets
import wambatic.reports.errors


def test_the_assets_are_the_five_files_the_page_loads_in_order() -> None:
    assert [asset.name for asset in wambatic.reports.assets.page_assets()] == [
        *wambatic.reports.assets.SCRIPT_NAMES,
        wambatic.reports.assets.STYLESHEET_NAME,
    ]
    media = {asset.name: asset.media_type for asset in wambatic.reports.assets.page_assets()}
    assert media['report.css'] == 'text/css; charset=utf-8'
    assert media['report.js'] == 'text/javascript; charset=utf-8'


def test_the_stylesheet_asset_has_its_palette_filled_in() -> None:
    css = next(a for a in wambatic.reports.assets.page_assets() if a.name == 'report.css')
    assert b'$light' not in css.content
    assert b'--surface: #fcfcfb;' in css.content


def test_the_folder_name_is_the_prefix_and_twelve_hex_digits_of_the_hash() -> None:
    digest = wambatic.reports.assets.assets_hash()
    assert len(digest) == 12
    assert int(digest, 16) >= 0
    assert wambatic.reports.assets.assets_folder_name() == f'wambatic-assets-{digest}'


def test_the_hash_changes_when_any_assets_content_or_name_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assets = wambatic.reports.assets.page_assets()
    original = wambatic.reports.assets.assets_hash()
    for index, asset in enumerate(assets):
        for changed in (
            wambatic.reports.assets.Asset(asset.name, asset.content + b' ', asset.media_type),
            wambatic.reports.assets.Asset(asset.name + 'x', asset.content, asset.media_type),
        ):
            altered = (*assets[:index], changed, *assets[index + 1 :])
            with monkeypatch.context() as patch:
                patch.setattr(wambatic.reports.assets, 'page_assets', lambda a=altered: a)
                assert wambatic.reports.assets.assets_hash() != original


def test_the_vendored_excel_writer_matches_the_recorded_checksum() -> None:
    vendor = importlib.resources.files('wambatic.reports') / 'vendor'
    content = (vendor / 'write-excel-file.min.js').read_bytes()
    assert hashlib.sha256(content).hexdigest() == wambatic.reports.assets.WRITE_EXCEL_FILE_SHA256
    assert wambatic.reports.assets.WRITE_EXCEL_FILE_VERSION == '4.1.1'
    assert b'MIT License' in (vendor / 'LICENSE').read_bytes()


def test_write_assets_writes_every_asset_under_the_hashed_folder(tmp_path: pathlib.Path) -> None:
    folder = wambatic.reports.assets.write_assets(tmp_path / 'a' / 'b')
    assert folder == tmp_path / 'a' / 'b' / wambatic.reports.assets.assets_folder_name()
    for asset in wambatic.reports.assets.page_assets():
        assert (folder / asset.name).read_bytes() == asset.content
    assert stat.S_IMODE(folder.stat().st_mode) == 0o755
    assert [path.name for path in folder.parent.iterdir()] == [folder.name]


def test_write_assets_keeps_an_existing_folder_holding_the_same_files(
    tmp_path: pathlib.Path,
) -> None:
    folder = wambatic.reports.assets.write_assets(tmp_path)
    marker = folder / 'marker'
    marker.write_text('mine')
    assert wambatic.reports.assets.write_assets(tmp_path) == folder
    assert marker.read_text() == 'mine'


def test_an_existing_folder_with_an_edited_file_is_refused(tmp_path: pathlib.Path) -> None:
    folder = wambatic.reports.assets.write_assets(tmp_path)
    (folder / 'report.js').write_text('planted')
    with pytest.raises(wambatic.reports.errors.OutputError) as caught:
        wambatic.reports.assets.write_assets(tmp_path)
    expected = f"cannot write {folder}: it exists and does not hold this version's files; remove it"
    assert str(caught.value) == expected
    assert (folder / 'report.js').read_text() == 'planted'


def test_an_existing_folder_that_is_a_symlink_is_refused(tmp_path: pathlib.Path) -> None:
    elsewhere = wambatic.reports.assets.write_assets(tmp_path / 'elsewhere')
    out = tmp_path / 'out'
    out.mkdir()
    (out / elsewhere.name).symlink_to(elsewhere)
    with pytest.raises(wambatic.reports.errors.OutputError, match='does not hold'):
        wambatic.reports.assets.write_assets(out)


def test_a_changed_asset_makes_a_second_folder_and_leaves_the_first(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = wambatic.reports.assets.write_assets(tmp_path)
    before = {
        asset.name: (first / asset.name).read_bytes()
        for asset in wambatic.reports.assets.page_assets()
    }
    assets = wambatic.reports.assets.page_assets()
    changed = wambatic.reports.assets.Asset('report.js', b'changed', assets[3].media_type)
    altered = (*assets[:3], changed, *assets[4:])
    monkeypatch.setattr(wambatic.reports.assets, 'page_assets', lambda: altered)
    second = wambatic.reports.assets.write_assets(tmp_path)
    assert second != first
    assert {path.name for path in tmp_path.iterdir()} == {first.name, second.name}
    assert {name: (first / name).read_bytes() for name in before} == before


def test_a_failed_write_leaves_no_folder_and_no_temporary_directory(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(source: object, destination: object) -> None:
        raise OSError(28, 'no space left')

    monkeypatch.setattr(os, 'rename', refuse)
    with pytest.raises(wambatic.reports.errors.OutputError) as caught:
        wambatic.reports.assets.write_assets(tmp_path)
    target = tmp_path / wambatic.reports.assets.assets_folder_name()
    assert str(caught.value) == f'cannot write {target}: no space left'
    assert list(tmp_path.iterdir()) == []


def test_a_folder_made_by_another_run_meanwhile_is_kept(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / wambatic.reports.assets.assets_folder_name()
    real_rename = os.rename

    def lose_the_race(source: pathlib.Path, destination: pathlib.Path) -> None:
        shutil.copytree(source, target)
        (target / 'theirs').write_text('theirs')
        real_rename(source, destination)

    monkeypatch.setattr(os, 'rename', lose_the_race)
    assert wambatic.reports.assets.write_assets(tmp_path) == target
    assert (target / 'theirs').read_text() == 'theirs'
    assert [path.name for path in tmp_path.iterdir()] == [target.name]


def test_a_folder_planted_meanwhile_with_other_files_is_refused(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / wambatic.reports.assets.assets_folder_name()
    real_rename = os.rename

    def plant(source: pathlib.Path, destination: pathlib.Path) -> None:
        target.mkdir()
        (target / 'report.js').write_text('planted')
        real_rename(source, destination)

    monkeypatch.setattr(os, 'rename', plant)
    with pytest.raises(wambatic.reports.errors.OutputError, match='does not hold'):
        wambatic.reports.assets.write_assets(tmp_path)
    assert [path.name for path in tmp_path.iterdir()] == [target.name]


def test_an_unwritable_directory_is_an_output_error(tmp_path: pathlib.Path) -> None:
    blocker = tmp_path / 'file'
    blocker.write_text('x')
    with pytest.raises(wambatic.reports.errors.OutputError, match='cannot write'):
        wambatic.reports.assets.write_assets(blocker / 'sub')
