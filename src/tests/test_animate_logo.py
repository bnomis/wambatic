"""Tests for bin/animate-logo.py, the rippling home-page logo built from the still mark."""

import importlib.util
import pathlib
import re
import types

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / 'bin/animate-logo.py'
BOX = '<rect x="0" y="0" width="180" height="180" rx="40" fill="#FFFFFF"/>'
CHECK = ['--check']
SQUARE = '<rect x="{x}" y="10" width="18" height="18" rx="3" fill="#cde2fb"/>'


def load_script() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location('animate_logo_script', SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


animate_logo = load_script()


def mark(*squares: str) -> str:
    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180">'
    return f'{head}{BOX}{"".join(squares)}</svg>'


def test_committed_logo_is_current() -> None:
    assert animate_logo.main(CHECK) == 0


def test_every_square_animates_and_the_box_does_not() -> None:
    animated = animate_logo.animate(mark(*(SQUARE.format(x=x) for x in (10, 40, 70))))
    assert animated.count('class="q"') == 3
    box = re.search(r'<rect[^>]*rx="40"[^>]*/>', animated)
    assert box is not None
    assert 'class' not in box.group(0)
    assert '@media (prefers-reduced-motion:reduce){rect.q{animation:none}}' in animated


def test_output_is_reproducible() -> None:
    still = mark(*(SQUARE.format(x=x) for x in (10, 40, 70)))
    assert animate_logo.animate(still) == animate_logo.animate(still)


def test_columns_darken_left_to_right() -> None:
    bands = [animate_logo.column_band(column, 7) for column in range(7)]
    assert bands == ['faint', 'faint', 'faint', 'medium', 'medium', 'strong', 'strong']


def test_bands_cycle_neighbouring_ramp_steps() -> None:
    ramp = animate_logo.RAMP
    assert [ramp.index(band[0]) for band in animate_logo.BANDS.values()] == [0, 1, 2]
    for band in animate_logo.BANDS.values():
        steps = [ramp.index(colour) for colour in band]
        assert steps == list(range(steps[0], steps[0] + 3))


@pytest.mark.parametrize(
    ('still', 'message'),
    [
        ('<svg', 'not valid SVG'),
        (mark(), 'no squares'),
    ],
)
def test_unusable_mark_is_refused(still: str, message: str) -> None:
    with pytest.raises(animate_logo.LogoError, match=message):
        animate_logo.animate(still)


def one_pair(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, still: str) -> pathlib.Path:
    """Point the script at one still drawing in tmp_path, and return its animated file's path."""
    source = tmp_path / 'still.svg'
    source.write_text(still, encoding='utf-8')
    target = tmp_path / 'animated.svg'
    monkeypatch.setattr(animate_logo, 'PAIRS', ((source, target),))
    return target


def test_both_drawings_have_an_animated_version() -> None:
    names = {(source.name, target.name) for source, target in animate_logo.PAIRS}
    assert names == {
        ('favicon.svg', 'favicon-animated.svg'),
        ('wambatic-mark.svg', 'wambatic-mark-animated.svg'),
    }


def test_missing_drawing_is_one_line_and_status_1(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = one_pair(tmp_path, monkeypatch, mark())
    monkeypatch.setattr(animate_logo, 'PAIRS', ((tmp_path / 'missing.svg', target),))
    assert animate_logo.main([]) == 1
    err = capsys.readouterr().err
    assert err.startswith('animate-logo: ') and err.count('\n') == 1


def test_unusable_drawing_names_its_file(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    one_pair(tmp_path, monkeypatch, mark())
    assert animate_logo.main([]) == 1
    assert capsys.readouterr().err == 'animate-logo: still.svg: no squares besides the box\n'


def test_check_reports_a_stale_file_without_writing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = one_pair(tmp_path, monkeypatch, mark(SQUARE.format(x=10)))
    target.write_text('old', encoding='utf-8')
    assert animate_logo.main(CHECK) == 1
    assert target.read_text(encoding='utf-8') == 'old'
    assert 'animated.svg stale' in capsys.readouterr().err


def test_writes_the_animated_drawing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    still = mark(SQUARE.format(x=10))
    target = one_pair(tmp_path, monkeypatch, still)
    assert animate_logo.main([]) == 0
    assert target.read_text(encoding='utf-8') == animate_logo.animate(still)
