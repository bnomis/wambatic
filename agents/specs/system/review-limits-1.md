# Review: the limits the system spec still accepts

**Date:** 2026-11-03
**Spec:** `agents/specs/system/spec.md` 1.12, "Limits accepted for the first release"
**Review page:** https://claude.ai/artifact/32inH8uRHaZ431h1xckGsA (choose an option for each decision there; answers are copied into Answers below)

## What is being reviewed and how

The system spec lists limits accepted for the first release. `/todo-review` files such a limit in `TODO.md` only once the user chooses to lift it; three were lifted that way on 2026-11-02 (Enterprise Server, the commit sync, one timezone per report) and are now built. The `/todo-review` of 2026-11-03 found four limits still accepted with no item. For each, decide whether to keep it as an accepted limit, or file it in `TODO.md` as work to do, which `/todo-do` would then take through a spec. Filing one commits to nothing more than a dated item; keeping one leaves the spec, `docs/limits.md` and the code as they are.

## Automatic checks

- Each limit is still stated in `agents/specs/system/spec.md` and `docs/limits.md`, checked 2026-11-03: pass.
- No open `TODO.md` item and no unfinished task in `agents/tasks/` covers any of them, checked 2026-11-03: pass.
- Measured on 2026-11-03 in the screenshot cache (`~/.cache/wambatic/docs.sqlite3`, the pallets organisation): 8,830 pull requests over 10 repositories, 5,410 of them merged, and 21,193 commits.

## The items

None: every question here is a decision, below.

## Decisions

### 1. Pull request sizes count generated files

- **What is being decided:** whether `pr_size_p50` should leave out generated files, as the `activity` line counts now do.
- **Background:** since commit sync 1.0 (built 2026-11-02) `lines_added` and its siblings leave out files matching `stats.exclude_paths` and linguist-generated files. `pr_size_p50`, the median size of the pull requests merged in a period (flow group, metric groups spec), still uses GitHub's own `additions + deletions` for each pull request. That was accepted as item 14 of the commit sync review, approved 2026-11-02, because a pull request's files are not in the cache.
- **What it affects:** a fix needs each merged pull request's file list: REST `GET /repos/{owner}/{name}/pulls/{number}/files`, one request per 100 files, at most 3,000 files. For the pallets cache that is at least 5,410 requests on a first sync, a little over an hour of the 5,000-an-hour REST budget, then one or more per newly merged pull request. It changes the fetch, cache (a new table and a schema raise), flow and metric groups specs.
- **Keep (recommended):** `pr_size_p50` stays GitHub's figure, named as a limit in `docs/limits.md`. Recommended because the cost is a request per merged pull request for one median, and a pull request's size is usually read alongside its review times, which do not depend on it.
- **File it:** a new `TODO.md` item; `/todo-do` starts a spec that weighs the REST file lists against reading pull request heads from the clones.

### 2. Linguist attributes are read at the default branch's head only

- **What is being decided:** whether each commit's generated files should be judged by the `.gitattributes` in that commit's own tree, and whether the `api-files` method's 3,000-file cap per commit should be worked round.
- **Background:** the commit sync reads `linguist-generated` and `linguist-vendored` once, at the default branch's current head, and applies them to every commit (commit sync review item 6, approved 2026-11-02, "as GitHub's language bar does"). An attribute added today also marks a file in old commits. Separately, the `api-files` method reads files by REST, which lists at most 3,000 files of a commit (item 18, approved 2026-11-02); a cloned repository has no cap.
- **What it affects:** per-commit attributes need one `git check-attr --source <commit>` per commit with changed paths instead of one per repository, local work only (21,193 commits in the pallets cache), and the `generated` flag would then differ from GitHub's own language bar. The cap affects only `api-files` repositories and only commits that touch more than 3,000 files.
- **Keep (recommended):** both stay accepted. Recommended because attributes rarely change, matching GitHub's view is a feature, and commits that large are rare and are mostly the generated files the filter exists to drop.
- **File it:** a new `TODO.md` item for per-commit attributes (and the cap, if you want it covered too); `/todo-do` starts a commit sync spec change.

### 3. GitHub Enterprise Cloud with data residency (`*.ghe.com`) is not supported

- **What is being decided:** whether wambatic should support Enterprise Cloud instances with data residency.
- **Background:** Enterprise Server support (fetch spec 1.16, built 2026-11-02) refuses a host ending in `.ghe.com` (fetch review 1, item 3, approved 2026-11-02), because such an instance's API lives at `api.<subdomain>.ghe.com`, not at the `/api/v3` path Enterprise Server uses, and sending requests there would fail confusingly.
- **What it affects:** support needs `GitHubHost` to give a `.ghe.com` host its own REST and GraphQL addresses and token variable, and fixtures recorded from a real data-residency instance to test it; nothing can be recorded without access to one.
- **Keep (recommended, unless you use such an instance):** the host stays refused with its clear message. Recommended because without an instance to record from, the support could not be tested.
- **File it:** a new `TODO.md` item; worth it only if you, or someone you build this for, has a `*.ghe.com` instance.

### 4. Commits read through the API carry no author offset

- **What is being decided:** whether to do more for commits of repositories that are not cloned, in the author-zone mode built on 2026-11-03.
- **Background:** measured on 2026-11-03, GitHub's GraphQL and REST APIs return every commit date in UTC, so only a cloned repository has each commit's offset. You chose on 2026-11-03 to date such commits in the report zone and name their repository in the report, rather than borrow an author's offset from another repository, which can be wrong across daylight saving or travel.
- **What it affects:** nothing more can be read from GitHub. What already covers it: `fetch.clone_repos` lets a private repository be cloned, which gives its offsets, and `stats.author_timezones` sets an author's zone by hand.
- **Keep (recommended):** it stays an accepted limit. Recommended because the two settings above already cover it, and any further fix would be a guess, which you declined on 2026-11-03.
- **File it:** a new `TODO.md` item to revisit inferring a zone, for example from the same login's cloned commits.

## Answers

Answered on the review page on 2026-11-03 at 16:06 UTC, with no comments:

- **Pull request sizes count generated files:** keep it accepted.
- **Linguist attributes are read at the default branch's head only:** keep it accepted.
- **Enterprise Cloud with data residency is not supported:** keep it accepted.
- **Commits read through the API carry no author offset:** keep it accepted.

No `TODO.md` item is filed for any of them.
