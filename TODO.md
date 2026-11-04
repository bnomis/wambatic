# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## A sync of pallets/flask stops on a GraphQL reply with no data

<!-- doc-counts: accept-start found on 2026-11-03 - a dated record, not a claim about the present -->
Found on 2026-11-03 while doing the screenshot item below: `bin/screenshots.sh`,
run twice against an emptied docs cache (`~/.cache/wambatic/docs.sqlite3`),
exited both times (about 19:45 and 19:57 UTC) with
`screenshots: MALFORMED: response has no data or lacks rateLimit`. Both times
the read in progress was "Reading all pull_requests of pallets/flask: no
previous sync"; every other repository's pull requests were synced, and
flask's were not (the schema 5 cache held 2,913 of them). Before each failure
GitHub's GraphQL replies took about 10 seconds and many were HTTP 502 (46 in
the first run, 17 in the second), each retried. The second run began flask's
read from the start again, so a re-run does not get further. The body of the
failing reply was not logged.
<!-- doc-counts: accept-end -->

Cause, suspected: GitHub's GraphQL timeout on the pull request page query
(`pullRequests(first: 100, ...)` in `src/wambatic/fetch/queries.py`), sent
once as a reply with neither `data` nor `errors`. `TRANSIENT_STATUSES` in
`src/wambatic/fetch/client.py` retries a 502, but `graphql` in the same file
raises `GraphQLError` `MALFORMED` for such a reply, which ends the sync. A
repository's full read keeps no progress between runs, so the same page
fails each time.

Fix direction: log the failing reply's status and body (with nothing
secret), then decide from it whether such a reply is transient (retried with
backoff like a 502), and whether the pull request page should shrink when
GitHub times out. If either changes the fetch spec's retry or paging rules,
it goes through the fetch spec first.

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

Note 2026-11-03: blocked by the item above; the re-run stops while syncing
pallets/flask's pull requests. The old schema 5 cache is kept outside the
repository until then.

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
