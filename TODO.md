# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## The oldest Enterprise Server release accepted is fixed at 3.19

Found on 2026-11-02 by `/todo-review`, from the fetch spec
(`agents/specs/fetch/spec.md`, "Server version"): `MIN_SERVER_VERSION` is
`(3, 19)`, the oldest Enterprise Server release GitHub supported on
2026-11-02, and "is raised by a release, not at run time". GitHub's "All
releases" page, read on 2026-11-02, gives 3.19 a closing date of 2026-12-09.
No item recorded raising it.

Cause: the constant in `src/wambatic/fetch/hosts.py` is set by hand, and
nothing reminds anyone when a release closes.

Fix direction: now, keep the closing down date of each supported release next
to `MIN_SERVER_VERSION` and add a test that fails once the release it names
has passed its closing down date, naming the release to raise it to; the
fetch spec's "Server version" section says so. Then, after 2026-12-09 (when
that test fails), re-read GitHub's "All releases" page, raise
`MIN_SERVER_VERSION` to the oldest release still supported, add any new
release's dates, and update the fetch spec's API block and the user guide
where they name the version.

Note 2026-11-04: a one-off routine, "wambatic: check GHES 3.19 closed"
(https://claude.ai/code/routines/trig_015ehYoX9t2H8Bm3uWpNE8xS), runs at
2026-12-10 09:00 UTC. It re-reads GitHub's "All releases" page and reports,
changing no file, whether `/todo-do` can raise `MIN_SERVER_VERSION`. Nothing
reminds anyone of the releases after 3.19.

### The code does not say when its minimum release has closed

<!-- doc-counts: accept-start found on 2026-11-04 - a dated record, not a claim about the present -->
Found on 2026-11-04, asked for by the user: a release closing should fail a
test, not wait on a reminder outside the repository. GitHub's "All releases"
page (https://docs.github.com/en/enterprise-server@latest/admin/all-releases),
read on 2026-11-04, lists the supported releases with a "Closing down date":
3.22 (released 2026-09-08, closing 2027-09-08), 3.21 (2026-06-11,
2027-06-11), 3.20 (2026-03-17, 2027-03-17) and 3.19 (2025-12-09,
2026-12-09), and says "GitHub supports at least the four most recent
feature releases". It does not define the closing down date; each release's
is a year after its release date. `src/wambatic/fetch/hosts.py` holds
`MIN_SERVER_VERSION` alone, with no dates, and the routine above covers 3.19
only.
<!-- doc-counts: accept-end -->
