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

Note 2026-11-04: wambatic now logs such a reply at `warning`, with its HTTP status and
the start of its body, before it stops (fetch spec 1.19). A probe of every page of
flask's pull requests (2026-11-04, 06:01-06:08 UTC) saw 502s after about 10.7 seconds
and secondary rate limits, all retried, and no such reply; the screenshot run that
followed synced flask in full. The decision waits for the next logged reply.

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
