# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## A report has one timezone

Found on 2026-11-02 by `/todo-review`, from the limits the system spec
(`agents/specs/system/spec.md`, "Limits accepted for the first release")
accepted for the first release: "one timezone per report". The user chose on
2026-11-02 to lift it.

Cause: bucketing takes a single `--tz` for every author and repository.

Fix direction: a spec change to `stats` and `reports`: a timezone per author
(from settings, or the commit's own offset), how buckets are formed when
authors are in different zones, and how the report says which zone each
figure uses.

Note 2026-11-02: since `1110cec` split the reports and stats specs, `--tz` is in the
`cli` spec and how a zone is shown is in the `terminal-report` and
`html-report` specs; bucketing stays in `stats`.

Spec: agents/specs/author-timezones/spec.md (1.0, with the amendments listed in its review); tasks: agents/tasks/author-timezones/tasks-1.md.

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
