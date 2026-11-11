# Review: tabbed HTML report and the GraphQL API

**Date:** 2026-11-11
**Spec:** `agents/specs/html-report/spec.md` (1.3 to 2.0) and `agents/specs/graphql-api/spec.md` (new, 1.0), with amendments to `agents/specs/web-app/spec.md` (1.1 to 2.0), `agents/specs/reports/spec.md` (1.15 to 1.16), `agents/specs/user-guide/spec.md` (1.0 to 1.1), `agents/specs/implementation-order.md` (1.13 to 1.14, step 16) and `agents/specs/index.md`
**Task list written against it:** none yet
**Review page:** https://claude.ai/artifact/BaQ21bUCmSLLHYA3i3NCXa (approve or flag each item there; answers are copied into Answers below)

## What is being reviewed and how

On 2026-11-11 the user found the HTML report page too long and asked for it to start with the summary tiles, then tabs for each section, long tables collapsed by default, sortable and filterable columns, and CSV and Excel export of each table; and for the web app's API to be GraphQL. In this session's interview the user chose: the Activity section split into Commits, Contributors and Lines tabs with Flow, Delivery and Popularity kept; a report that only has to open in a browser, with its scripts in an assets folder beside the page rather than inlined or loaded from a CDN; `write-excel-file` for Excel; Strawberry for GraphQL; and GraphQL replacing the REST routes rather than sitting beside them. The specs settle the rest. Each item below is a choice I made in writing them: approve it, or flag it with a comment saying what to change.

## Automatic checks

- Every relative link in the amended specs and this review resolves to a file: pass.
- No non-ASCII punctuation (dashes, curly quotes, ellipses) in the amended specs: pass.
- `pre-commit run` over the amended specs: pass.
- `bin/audit-check.sh` (the whole-tree audit, including spec signature drift): **fails, as expected while the spec is ahead of the code**: `spec-api-signature-drift` on `html_document` (the spec adds `assets_url`). It passes once the code is built, so the spec commits can be pushed only together with the implementation, or the pre-push hook refuses them.
- strawberry-graphql 0.341.2 does not list Python 3.14 in its PyPI classifiers (checked 2026-11-11): **needs attention**. The implementation order makes installing it under 3.14 and running its tests the first thing built (item 17).
- No code has been written; the task list's tests are the first check of the behaviour.

## The items

1. **The tabs.** Commits (commits and active days per period, the daily calendar, Activity by period), Contributors (contributors per period, top contributors, by author, by repository), Lines (lines added and deleted per period), Flow, Delivery and Popularity. A tab appears only when it has content, as a section does today.
2. **The Lines tab holds one chart.** The Activity by period table, which also has the line columns, stays in Commits, so it appears once. The Lines tab is short as a result.
3. **Unavailable stays outside the tabs**, below the panels, so a missing metric is never hidden in a tab not shown.
4. **The open tab is in the URL** (`#tab-flow`), set with `replaceState`, so a link opens on a tab and the back button does not step through tabs. Arrow keys, Home and End move between tabs (the WAI-ARIA tabs pattern). Without script every panel shows in order, as the page reads today.
5. **Charts are drawn when their tab first shows**, because Plotly sizes a chart in a hidden panel to zero width; a granularity change redraws the shown tab at once and the others when they next show.
6. **The assets folder is named by its content hash**, `wambatic-assets-<12 hex digits>/` beside the page, and is never changed once written; a newer wambatic adds a new folder beside it. A page copied without its folder shows a notice saying which folder it needs, and its tables still show.
7. **Every table is collapsible**, in a `<details>` block whose summary gives the title and row count; it starts open at 10 rows or fewer, closed above that. Unavailable is the exception (item 3).
8. **Sorting.** A click on a column header sorts ascending, then descending, then back to the original order; numbers sort by value with empty values last both ways, text in natural order ignoring case; the total row stays at the bottom.
9. **Filtering.** One input per column. Text columns match a substring, ignoring case; number columns take `N`, `>N`, `>=N`, `<N`, `<=N` or `A..B`. Filters combine with AND, a `Showing 37 of 412 rows` line updates, and the total row is relabelled `Total (all rows)` while a filter is on, so it is not read as the total of the rows shown.
10. **Export takes the rows shown**, filtered and in their sorted order, with the header and without the total row. CSV is UTF-8 with a byte order mark so Excel reads non-ASCII logins, numbers are written without separators, and a text cell starting with `=`, `+`, `-` or `@` gets a leading `'` so a spreadsheet cannot run a login as a formula.
11. **Excel through a vendored copy of `write-excel-file` 4.1.1** (MIT, about 70 KB) in `src/wambatic/reports/vendor/`, with its version and SHA-256 recorded and checked by a test, so an upgrade is always deliberate.
12. **openpyxl as a development dependency**, for the browser test to read an exported `.xlsx` back. Its last release was 2024-06-28; it is feature-complete, and is used only in tests.
13. **The GraphQL schema types the series, and leaves tables and provenance as JSON.** A client can pick series by metric and breakdown; the tables, whose columns differ by group, come as one JSON value each, exactly as `report --format json` gives them.
14. **The `stats` query never starts a sync.** On stale data it returns `SyncNeeded`, and a client calls the `sync` mutation, polls `job`, then queries `stats` with the job id. This keeps queries free of side effects; it is one round trip more than `/api/stats`, which started the sync itself.
15. **Errors arrive in GraphQL's `errors` list** with `extensions.code` (`BAD_REQUEST`, `NOT_FOUND`, `UPSTREAM`, `INTERNAL`, `BAD_QUERY`) and `extensions.status`, the HTTP status the web app maps the same error to, with HTTP 200 for the response; messages are redacted and never hold a traceback.
16. **A POST to `/graphql` must be `application/json`, or it gets 415.** Otherwise any website you visit could make your browser post a form to the local server and start a sync with your token; a browser sends JSON cross-site only after a preflight the server never approves.
17. **strawberry-graphql pinned exactly at 0.341.2**, because it is before 1.0 and releases often; the first task checks that it works under Python 3.14 and stops if it does not.
18. **GraphiQL replaces `/docs`.** Like Swagger UI today, it loads its script from a CDN, so it needs a network connection; the rest of the app does not. `/api/stats`, `/api/progress`, `/openapi.json` and `/docs` answer 404.
19. **The sync jobs move to `jobs.py`**, unchanged, so the API and the web pages share them without importing each other.
20. **The user guide spec gains the new behaviour**: the HTML page covers the folder, tabs, tables and export, and the web app page covers the GraphQL API with `curl` examples, GraphiQL and the JSON content type, with new screenshots.

## Decisions

None open. The choices the change needed were answered in this session's interview on 2026-11-11 and are recorded above.

## Answers

Answered on the review page on 2026-11-11: every item (1 to 20) approved, with no comments.
