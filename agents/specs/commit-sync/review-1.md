# Review: commit sync 1.0, commits from bare clones

**Date:** 2026-11-02
**Spec:** `agents/specs/commit-sync/spec.md` (new, 1.0), with amendments to `agents/specs/fetch/spec.md` (1.16 to 1.17), `agents/specs/cache/spec.md` (1.1 to 1.2), `agents/specs/stats/spec.md` (1.10 to 1.11), `agents/specs/metric-groups/spec.md` (1.0 to 1.1), `agents/specs/system/spec.md` (1.10 to 1.11), `agents/specs/cli/spec.md` (1.1 to 1.2), `agents/specs/terminal-report/spec.md` and `agents/specs/html-report/spec.md` (1.1 to 1.2), and `agents/specs/implementation-order.md` (1.11 to 1.12, step 14)
**Task list written against it:** none yet
**Review page:** https://claude.ai/artifact/Ry36e9NmJ6H31hdEZAscwB (approve or flag each choice there; answers are copied into Answers below)

## What is being reviewed and how

The system spec accepted two limits for the first release: only the default branch's history is counted, and line counts include generated files. On 2026-11-02 the user chose to lift both (`TODO.md`, "The commit sync reads only default-branch totals"). The amendments read commits from a local bare clone of each repository, which gives per-file line counts and every branch for free, and keep GraphQL only to map new commits to GitHub logins. The four design decisions were answered on 2026-11-02 through the question tool and are recorded under Answers. What remains is the choices made while writing the amendments, listed under The items: approve each, or flag it with a comment saying what to change. Work on the task list stops until every item has an answer.

## Automatic checks

- `git diff --check` over the amended specs: pass.
- Every relative link in the specs and this review resolves to a file: pass.
- pre-commit on the changed files (end-of-file and trailing-whitespace hooks; no code changed): pass.
- Measurements the design rests on, taken on 2026-11-02:
  - the pallets cache (`~/.cache/wambatic/docs.sqlite3`): 11 repositories, 21,193 default-branch commits, which GitHub's own history counts confirm; the REST budget was 5,000 an hour: pass, as the spec says;
  - REST `GET /repos/pallets/flask/commits/{sha}` returns `files[]` with `filename`, `additions` and `deletions`, at one request per commit: pass;
  - bare clones: flask 3 s and 13 MB, werkzeug 4 s and 19 MB; `git log --numstat` over all branches 1 s and 2 s; per-file rows 9,500 and 13,223: pass;
  - lock, `requirements*.txt`, `vendor/` and minified files: 6.7% of flask's and 3.5% of werkzeug's non-merge default-branch lines: pass;
  - branches: flask 4 (2 commits not on `main`), werkzeug 2 (none): pass.
- `git check-attr --source` is in git's 2.40 release notes (read 2026-11-02), and `git check-attr -z --stdin --source <head>` ran on the flask clone with git 2.56.0: pass.
- `git log -z -M --diff-merges=first-parent --numstat` with the spec's format string parsed on the flask clone: pass.
- `PurePosixPath.full_match` on Python 3.14 matches `uv.lock` and `a/b/yarn.lock` with `**/*.lock`, and `src/vendor/y/z.c` with `**/vendor/**`, and leaves `src/app.py` unmatched: pass.
- `bin/audit-check.sh`: pass, after three `spec-api-signature-drift` acceptances in the cache spec: `inspect_cache` and `clear_cache` take the proposed `clones_dir` (the task list removes those two markers when step 14 builds it), and `Cache.read_commits`, which the checker matched by name with `stats.read_commits` once it gained a docstring.
- No live sync through a clone has been run yet; the first is the task list's live test: **needs attention** (item 14).

## The items

1. **The clone replaces the GraphQL history and the REST compare entirely.** One source for the commit graph, not two that must agree: git lists the commits, their parents, dates and per-file counts, and GraphQL only looks up each new commit's author login by oid, 100 per query, the same cost as the history paging it replaces. `COMMIT_HISTORY`, `COMMIT_COUNTS` and `Fetcher.compare` go.
2. **Rewrite detection is a set difference.** The commits a repository should hold are those reachable from its followed heads; new ones are added and the rest deleted. A force-push, a rewritten history, a deleted branch and a pattern removed from `fetch.branches` are all the same case, with no per-branch ancestor check and no full re-read.
3. **The token reaches git through the environment only.** `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0=http.extraHeader` and `GIT_CONFIG_VALUE_0=Authorization: Basic <base64 of x-access-token:TOKEN>`, never in an argument, a URL or the clone's config; prompts and credential helpers are off; standard error is redacted for the token and its base64 form. A test checks that no argument holds it.
4. **Clones live beside the cache file and go with it.** `~/.cache/wambatic/clones/cache/` for github.com, `clones/cache-<host>/` for an Enterprise host, `fetch.clone_dir` to move them; `wambatic cache clear` deletes them, and `cache info` reports their size. They hold `refs/heads/*` only.
5. **Counts match GitHub's own totals.** Renames are detected (`-M`), so a moved file is not a full delete and add; a merge commit is counted against its first parent; a binary file is stored with zero counts and `binary` set.
6. **Linguist attributes are read at the default branch's current head**, and applied to every commit's paths. Every flag is recomputed when any `.gitattributes` in that tree changes (a probe of their paths and blob oids). An accepted limit: an attribute added today also marks a file in old commits, as GitHub's language bar does.
7. **The default `stats.exclude_paths`**: `**/*.lock`, `**/package-lock.json`, `**/pnpm-lock.yaml`, `**/go.sum`, `**/vendor/**`, `**/node_modules/**`, `**/dist/**`, `**/*.min.js`, `**/*.min.css`, `**/*.map`. `requirements*.txt` is left out of the defaults, because many are written by hand.
8. **Branch patterns are `fnmatch` globs, and the default branch is always followed.** `()` is the default branch only, `('*',)` every branch. The patterns are recorded in the commit state's `probe`, so changing the setting re-syncs every repository on the next run even when nothing was pushed.
9. **A report never mixes branch settings.** A `--no-fetch` or `--max-age` run after `fetch.branches` changed raises `BranchesMismatchError`, naming the repositories and both pattern lists, rather than warning and carrying on.
10. **Author emails are never stored.** git knows each commit's email; only the GitHub login from GraphQL is kept, as today.
11. **A commit whose every file is left out still counts** in `commits`, `contributors` and `active_days`, with no lines: the setting changes what a line is, not what a commit is.
12. **One schema raise, to 5, with no migration.** A cache of 4 holds totals only, so it is refused once with the usual message and its commits are refetched through clones.
13. **`git` 2.40 or later on `PATH`, and no Python git library.** `check-attr --source` needs 2.40; subprocess calls through asyncio keep the dependency list as it is. `GitError` is raised when git is missing or older, naming the version found.
14. **Pull request sizes keep GitHub's totals.** `pr_size_p50` still includes generated files, an accepted limit, named in the system and metric-groups specs. No live sync through a clone has been run yet, so the task list's live test on `octocat/Hello-World` is the first real check against `stats/code_frequency`.

## Revision after the flag on item 1

The user flagged item 1 on the review page on 2026-11-02 at 20:07 UTC: "This should only happen for open source projects or projects where the user has given explicit permission to clone the repo. Otherwise fallback to only default branch and as an explicit option slow history via gql and rest". Four follow-up decisions were answered the same day through the question tool (see Answers), and the spec now reads each repository's commits by one of three methods: `clone` for a public repository or one allowed by `fetch.clone_repos`, `api` (the 1.16 sync, kept) for any other, and `api-files` when `fetch.api_history` is `'files'`. Items 2 to 14 still hold for the cloned repositories. The choices made while revising, to approve or flag:

15. **Visibility decides, and only a positive answer clones.** The listing now selects each repository's `visibility`. A repository is cloned only when it is `PUBLIC` or its `owner/name` matches a `fetch.clone_repos` pattern (compared lower-cased); `INTERNAL`, an Enterprise visibility, counts as not public; a `Repo` built without the field defaults to `PRIVATE`, so a missing value never clones.
16. **The 1.16 sync is kept unchanged as the `api` method.** Default branch, GraphQL history and REST compare, per-commit totals, no files; `COMMIT_HISTORY` and `COMMIT_COUNTS` stay; `fetch.branches` does not apply to it.
17. **`api-files` reads branches with GraphQL and files with REST.** `BRANCHES` lists the heads; a moved head is read with `compare`, a new branch with `BRANCH_HISTORY`; a rewrite, a 404 or a branch dropped reads every followed branch in full, because only that shows which cached commits no branch reaches. Each new commit's files come from REST `GET /commits/{sha}`, paged past 300 files; a commit's totals stay GitHub's, and a cached commit is never read again.
18. **`api-files` has no linguist attributes, and keeps GitHub's 3,000-file cap.** Without a clone `generated` is False on every file and only `stats.exclude_paths` applies; a commit touching more than 3,000 files counts only the files REST lists (GitHub's REST reference, checked 2026-11-02). Both are accepted limits.
19. **A report names every repository it could not filter.** `tables['unavailable']` gets a row per `api` repository (generated files counted; and default branch only when `fetch.branches` is set) and per `api-files` repository with `stats.linguist` on (attributes not read). The provenance gains `commit_methods`, and the terminal and HTML footers a line `Commits read by: ...`. Stats picks files or totals by the recorded method, never by whether a commit happens to have files.
20. **The method is recorded, and a change re-reads.** The commit state's `probe` begins `method=<method>`; a different method at the next sync (made public or private, a pattern added or removed, `fetch.api_history` changed) re-reads the repository in full in the new method, replacing its rows, and a repository that may no longer be cloned has its clone removed.

## Decisions

None open. The four decisions this change needed were answered on 2026-11-02 and are recorded below.

## Answers

Answered on 2026-11-02 through the question tool, before the amendments were written:

- **Where per-file line counts come from:** a local bare clone of each repository, kept and fetched each sync, with GraphQL only mapping commits to logins.
- **Which branches are followed by default:** the default branch only; `fetch.branches` names more, so existing reports keep their numbers.
- **Which files count as generated:** a built-in, editable pattern list (`stats.exclude_paths`) plus the files a repository marks `linguist-generated` or `linguist-vendored`.
- **When excluded files are filtered:** at report time; the cache keeps every file's counts, and the provenance records the patterns used.

Item verdicts, answered on the review page on 2026-11-02 between 20:04 and 20:07 UTC: items 2 to 14 **approved**, with no comments; item 1 **flagged**, with the comment quoted under Revision after the flag on item 1.

Follow-up decisions on the flag, answered on 2026-11-02 through the question tool:

- **How permission to clone is given:** a pattern list, `fetch.clone_repos` (`owner/name` patterns, default empty); public repositories are cloned without it.
- **What the slow API option reads:** per-file counts and the followed branches: `fetch.api_history`, `'totals'` by default, `'files'` to read each commit's files by REST and follow `fetch.branches`.
- **A report over both kinds of repository:** counts both, and names in `tables['unavailable']` and the footers the repositories whose lines could not be filtered or whose other branches were not counted.
- **A repository whose method changes:** read again in full in the new method; its rows never mix methods, and a clone it may no longer keep is removed.

Revision items 15 to 20, answered on the review page on 2026-11-02 at 20:28 UTC: all **approved**, with no comments. Item 1 stays flagged as the record of the comment; items 15 to 20 settle it.
