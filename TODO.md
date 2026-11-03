# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## The screenshot cache and the cache info image are still at schema 5

Found on 2026-11-03 by `/todo-review`, from the author timezones task list
(`agents/tasks/author-timezones/tasks-1.md`, Task 6 notes): "The screenshot
cache (`~/.cache/wambatic/docs.sqlite3`) is at schema 5 and will be refused
by the next `bin/screenshots.sh` run; this list does not re-run it". On
2026-11-03 the cache's `meta` table recorded `schema_version` 5 while
`SCHEMA_VERSION` in `src/wambatic/fetch/cache.py` is 6, and the published
`docs/images/terminal/cache-info.svg` shows `schema_version 5`, though the
guide now describes schema 6.

Cause: cache schema 6 (author timezones spec 1.0, cache spec 1.3) refuses an
older cache with no migration, and `bin/screenshots.py` opens the docs cache
without clearing it, so its run exits with `CacheVersionError`.

Fix direction: clear the docs cache, re-run `bin/screenshots.sh` (it needs a
GitHub token and the network), and commit the regenerated images, the
`cache info` one included.

## The oldest Enterprise Server release accepted is fixed at 3.19

Found on 2026-11-02 by `/todo-review`, from the fetch spec
(`agents/specs/fetch/spec.md`, "Server version"): `MIN_SERVER_VERSION` is
`(3, 19)`, the oldest Enterprise Server release GitHub supported on
2026-11-02, and "is raised by a release, not at run time". GitHub's "All
releases" page, read on 2026-11-02, gives 3.19 a closing date of 2026-12-09.
No item recorded raising it.

Cause: the constant in `src/wambatic/fetch/hosts.py` is set by hand, and
nothing reminds anyone when a release closes.

Fix direction: after 2026-12-09, re-read GitHub's "All releases" page, raise
`MIN_SERVER_VERSION` to the oldest release still supported, and update the
fetch spec's API block and the user guide where they name the version.
