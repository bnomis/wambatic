# Tasks: User guide

**Spec:** `agents/specs/user-guide/spec.md`
**Created:** 2026-11-01
**Version:** 1

The guide is new, so no task is done yet. `docs/`, `mkdocs.yml`, `bin/screenshots.py` and
`src/tests/test_docs.py` do not exist (checked 2026-11-01).

The docs tools live in the `docs` dependency group, which a plain `uv sync` removes again. Every task
that builds the site runs `uv sync --group docs` first. Every `mkdocs` command below runs after
`source bin/activate.sh`.

Task 4 needs a GitHub token and Playwright's Chromium on the machine that runs it. Without them it
stops as `blocked`, naming the command for the operator to run.

---

## Task 1: Scaffold the MkDocs site, theme and docs workflow

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** Module location; Implementation (`mkdocs.yml`, Theme, Logo, Light and dark, Dependencies, CI)

**Technical Goal:** A site that builds strictly and deploys, with metafopy's look, before any content is written.

**Subtasks:**

- [x] `uv add --group docs mkdocs mkdocs-material`, then check that `pyproject.toml` and `uv.lock` both changed, and nothing else did
- [x] Add `site/` to `.gitignore`
- [x] Write `mkdocs.yml` as the spec's Implementation says:
  - `site_name`, `site_description`, `site_url: https://bnomis.github.io/wambatic/` and `repo_url`
  - Material with the logo and favicon, Mona Sans and Source Code Pro, and the features `navigation.sections`, `navigation.top`, `content.code.copy` and `content.code.annotate`
  - the palette toggle with a light and a dark scheme
  - the extensions `admonition`, `attr_list`, `md_in_html`, `tables`, `toc` (permalink), `pymdownx.highlight`, `pymdownx.snippets` (`base_path: docs/snippets`, `check_paths: true`) and `pymdownx.superfences`, the last with the `mermaid` custom fence from the Material diagrams page
  - `plugins: [search]`
  - the full nav of the spec's Pages table, in order
- [x] Write `docs/assets/theme.css`: metafopy's colour variables, header rule and search-box rules, with its colour comment. Leave out its `.compare`, `.plots`, `.doc-contents` and `details.metafor-reference` rules. Add a `[data-md-color-scheme="slate"]` block whose colours keep the same hues on a dark ground
- [x] Draw `docs/assets/wambatic-mark.svg` (three or four rising bars in a hairline box; graphite `#3D3F44`, one bar Solarized blue `#268BD2`) and `docs/assets/favicon.svg` (the same mark, legible at 16 px)
- [x] Create each page in the nav as a stub: an H1 and the one sentence saying what the page is for, from the spec's Pages table. Then `docs/snippets/captured.md` with one line, "Screenshots not captured yet."
- [x] Write `.github/workflows/docs.yml` on the pattern of the spec's CI paragraph:
  - triggers: pull requests, pushes to main touching `docs/**`, `mkdocs.yml`, `pyproject.toml`, `uv.lock` or the workflow, and `workflow_dispatch`
  - `permissions: contents: write`, and a concurrency group
  - the `actions/checkout` and `astral-sh/setup-uv` versions and comments of `.github/workflows/ci.yml`, with `submodules: false`
  - `uv sync --locked --group docs`
  - on pull requests, `uv run mkdocs build --strict`; otherwise, after setting the bot's git identity, `uv run mkdocs gh-deploy --strict --force --no-history --remote-branch gh-pages`
- [x] Add `docs` (the user guide) to `AGENTS.md`'s Layout. Add the docs workflow to its Checks, and `mkdocs`/`mkdocs-material` (the `docs` group, `uv sync --group docs`) to its Tools

**Acceptance Criteria:**

- [x] `mkdocs build --strict` exits 0 with every nav entry present
- [x] `git status --porcelain` lists no file under `site/`
- [x] The built `site/index.html` references `assets/theme.css` and the logo

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_package.py` passes

**Notes:**

- Material diagrams: <https://squidfunk.github.io/mkdocs-material/reference/diagrams/>. The palette toggle: <https://squidfunk.github.io/mkdocs-material/setup/changing-the-colors/#color-palette-toggle>
- The metafopy files to follow are restated here, not linked: its theme sets
  - `--md-primary-fg-color: #FFFFFF`
  - `--md-primary-bg-color: #3D3F44`
  - `--md-accent-fg-color: #1C6FA9`
  - `--md-typeset-a-color: #268BD2`
  - footers `#3D3F44`
  - a `1px solid #D8D9DC` header border with no shadow
  - a `#F4F4F5` search box with a `#D8D9DC` border and a `0.4rem` radius, above 60em
- The audit's dependency check D2 may flag the two new packages. That is handled in Task 10, not here

---

## Task 2: Write the reference pages and the drift test

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** Pages (`reference/*`); API (`test_docs.py`); Drift test

**User Story:** As a user, I want reference tables I can trust, so that an option or default I read is the one the program has.

**Subtasks:**

- [x] Write `src/tests/test_docs.py`, with `doc_table(page, heading)` reading the first Markdown table under a heading, keyed by column header. It ignores backticks, and splits cells holding several names (`-v`, `--verbose`)
- [x] `test_cli_options_match`: each command's table in `docs/reference/cli.md` lists exactly the options of its dataclass in `wambatic.cli`. The tables are global (`Wambatic`), `report` (`Report`), `serve` (`Serve`) and `cache` (`CacheCommand`). Option names come from the `cappa.Arg` metadata (long form `--kebab-case`, any short form); positionals are the upper-case field name; `-h`/`--help` and `--completion` are allowed extra rows in the global table
- [x] `test_settings_match`: `docs/reference/settings.md` has a row per field of `FetchSettings`, `StatsSettings` and `ReportSettings`, named `section.field`, and no other rows. Each documented default parses back to the dataclass default as the spec's Drift test section says
- [x] `test_metrics_match`: each metric row in `docs/reference/metrics.md` has the name, group and unit of the following, and every metric has a row:
  - `wambatic.stats.activity.TOTAL_METRICS`
  - `wambatic.stats.flow.FLOW_METRICS`
  - `wambatic.stats.delivery.DELIVERY_METRICS`
  - `wambatic.stats.popularity.POPULARITY_METRICS`
- [x] `test_groups_match`: the groups listed in `reference/metrics.md` equal `wambatic.stats.base.GROUPS`
- [x] Write `docs/reference/cli.md`, `settings.md` (with a Type column), `metrics.md` and `exit-statuses.md` from the README's tables, extending them where the drift test finds a gap. Write each metric's definition in full, so the guide pages can link to it
- [x] Run each new test once against a deliberately wrong page (a row removed, a default changed), and confirm it fails and names the row. Then restore the page
- [x] Add `test_docs.py` to `AGENTS.md`'s list of test-layout exceptions

**Acceptance Criteria:**

- [x] Every test in `src/tests/test_docs.py` passes, and fails when one documented row is removed or one default is changed
- [x] The test imports no MkDocs package, so it runs in CI's `check` job without the `docs` group

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_docs.py src/tests/test_cli.py src/tests/test_settings.py` passes

**Notes:**

- Depends on Task 1
- Cappa reads options from `typing.Annotated[..., cappa.Arg(...)]`. Use `typing.get_type_hints(cls, include_extras=True)` and the `cappa.Arg` objects' `short`/`long` fields. Where `long=True`, the name is derived from the field
- `wambatic.settings.parse_duration` reads `30d`, `1h` and `0s`

---

## Task 3: Write the screenshot script

**Status:** done
**Priority:** high
**Complexity:** large
**Spec Reference:** Screenshots; API (`bin/screenshots.py`); Error handling

**Technical Goal:** One command that rebuilds every screenshot from real data, so the images can be refreshed whenever the output changes.

**Subtasks:**

- [x] Write `bin/screenshots.py` (executable, `#!/usr/bin/env python3`, argparse with `--out docs/images` and `--skip-sync`) and its wrapper `bin/screenshots.sh` on the pattern of `bin/audit-check.sh`
- [x] Write a temporary config, setting `fetch.cache_path` to `~/.cache/wambatic/docs.sqlite3` and `stats.timezone` to `UTC`, and point `WAMBATIC_CONFIG` at it for every wambatic call the script makes, in-process and as a subprocess
- [x] Sync and compute through the same function the CLI uses (`wambatic.reports.service`), for:
  - `repo:pallets/click`
  - `org:pallets` with `--by-author`
  - groups `activity,flow,delivery,popularity`
  - `--since 2024-11-01 --until 2026-10-31 --by month`
  - the two date bounds and the subjects as constants at the top of the script
- [x] `capture_terminal`: render with `rich.console.Console(record=True, width=110, force_terminal=True)`, write `docs/images/terminal/<subject>-full.svg`, and split the record at each `heading` into `docs/images/terminal/<subject>-<section-slug>.svg`. Also capture `wambatic cache info` as `cache-info.svg`
- [x] `capture_html`: write the HTML report with `--out` into a temporary directory. In Playwright Chromium at 1280x800, write full-page `html/<subject>-light.png` and `-dark.png` (`color_scheme`), then one crop for each entry of a `SELECTORS` table at the top of the script: the tiles, the period switch, the calendar, a chart with a partial period, the delivery charts, the popularity charts, the languages chart. Take the selectors from `src/wambatic/reports/templates/report.html` and `report.js`
- [x] `capture_web`: start `wambatic serve --port <free> --max-age 30d` as a subprocess and wait for the port (30 s limit). Capture `web/form.png`, `web/report.png` and `web/api-docs.png`, then stop it. For `web/progress.png`, start a second server on an empty temporary cache, request `org:pallets` and capture once the page shows "Syncing repositories"
- [x] Write `docs/snippets/captured.md`: "Screenshots captured on `<UTC date>` from `pallets/click` and `org:pallets` with wambatic `<version>`, covering `<since>` to `<until>`."
- [x] Error handling as the spec's Error handling section says, each case one line on stderr and exit 1:
  - no token;
  - no Chromium;
  - a wambatic error;
  - a selector matching nothing;
  - a server not answering;
  - a file over 1 MB
- [x] Write `src/tests/test_screenshots.py` (no network; mark Chromium tests `browser`):
  - the SVG section split on a recorded console with two headings;
  - the selector table against an HTML report built from `tests.fixtures.reports`: every selector matches;
  - the 1 MB check;
  - a missing token naming the fix
- [x] Add `bin/screenshots.py` to `pyproject.toml`'s `per-file-ignores` for `T20` only if it prints, as `bin/record-fixtures.py` does

**Acceptance Criteria:**

- [x] `bin/screenshots.sh --help` prints the usage
- [x] Every test in `src/tests/test_screenshots.py` passes, the browser ones included where Chromium is installed
- [x] The script never reads or writes the user's own cache: the only `cache_path` it sets is the docs cache or a temporary one

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `bin/audit-check.sh --path bin` exits 0
- [x] `pytest src/tests/test_screenshots.py` passes

**Notes:**

- Depends on Task 1
- Rich's recorded export: `Console.export_svg(title=...)`. Splitting is easier if each section is rendered into its own recording console, by calling the section functions of `wambatic.reports.terminal` in the order `render_terminal` calls them. Keep the split in one function so it follows `render_terminal`'s order
- The browser test pattern (a uvicorn server on a free port, Playwright sync API) is in `src/tests/reports/test_web_browser.py`
- Never print or log the token; check for it with `wambatic.fetch.auth`, the module the CLI uses

---

## Task 4: Capture the screenshots

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** Screenshots

**Technical Goal:** Commit the images the guide pages embed.

**Subtasks:**

- [x] Check for the inputs without printing them: `[ -n "${GITHUB_TOKEN:-}" ] || gh auth token >/dev/null 2>&1` and `python -c 'import playwright.sync_api; playwright.sync_api.sync_playwright().start().chromium.launch().close()'`. If either is missing, stop the task as `blocked` and name the command for the operator to run, `bin/screenshots.sh`
- [x] Run `bin/screenshots.sh`
- [x] Look at every image once, and check it shows what its name says. If one shows an error, an empty chart or a cut-off section, fix the script (Task 3's code) and run it again
- [x] Commit `docs/images/` and `docs/snippets/captured.md`

**Acceptance Criteria:**

- [x] Each file the script names exists under `docs/images/`, and none is over 1 MB
- [x] `docs/snippets/captured.md` names the capture date and the wambatic version

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `git diff --cached --stat` shows no file over 1 MB

**Notes:**

- Depends on Task 3
- If the operator ran the script by hand, this task checks the images, and commits them if they are not committed yet

---

## Task 5: Write the opening pages

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** Pages (`index.md`, `install.md`, `token.md`, `getting-started.md`, `concepts.md`); Introduction (audience)

**User Story:** As an experienced git user new to wambatic, I want to install it, get a token and read my first report, so that I can see what it does within minutes.

**Subtasks:**

- [x] `index.md`: the pitch, one command, the light HTML screenshot, where to start (every guide page linked), why wambatic, its limits in one line each
- [x] `install.md`: Python 3.14 and uv, each with a link to its installer; clone, `uv sync`, `source bin/activate.sh`, checking `wambatic --help`; shell completion; updating
- [x] `token.md`: what a token is; the classic scopes and the fine-grained permissions (repository metadata and contents read, pull requests, issues and Actions read, organisation members read); `gh auth token`; never stored or printed; when no token is needed. Add the token-lookup flowchart
- [x] `getting-started.md`: the first report on `repo:pallets/click`, one terminal section screenshot per part, each explained; a warm re-run; the same as HTML and JSON
- [x] `concepts.md`: the architecture flowchart, the incremental-sync sequence diagram, rate limits and `fetch.on_rate_limit`
- [x] Include `captured.md` (`--8<-- "captured.md"` in a `note` admonition) on every page with a screenshot
- [x] Link each external term to its primary source the first time it appears on a page, as the spec's Introduction lists

**Acceptance Criteria:**

- [x] Each page has the diagrams and screenshots the spec's Pages table lists for it
- [x] Each command shown is one wambatic accepts: its options are in `reference/cli.md`
- [x] No sentence counts things a generator does not produce (the shared counts-in-prose rule): name the members or drop the number

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_docs.py` passes

**Notes:**

- Depends on Tasks 2 and 4
- The README holds the current text for each topic; move it here and expand it, without changing what it says the program does. Where the README and the code disagree, the code wins, and the task notes the difference in its commit body

---

## Task 6: Write the guide pages on targets, periods and the three front ends

**Status:** done
**Priority:** high
**Complexity:** large
**Spec Reference:** Pages (`guide/targets.md`, `guide/periods.md`, `guide/terminal.md`, `guide/html.md`, `guide/web.md`)

**User Story:** As a user, I want each way of choosing and viewing a report explained with pictures, so that I can pick the one I need.

**Subtasks:**

- [x] `targets.md` with the target flowchart
- [x] `periods.md` with the Mermaid `gantt` of a range cut into months
- [x] `terminal.md`: every section, in output order, each with its screenshot
- [x] `html.md`: the light and dark full pages and the crops the spec lists
- [x] `web.md`:
  - the form, progress, report and `/docs` screenshots;
  - the job state diagram;
  - the `/api/stats` sequence diagram;
  - the `Host`-check flowchart, with a link on DNS rebinding;
  - the README's security text in full
- [x] Include `captured.md` on each page with a screenshot, and link external terms as in Task 5

**Acceptance Criteria:**

- [x] Each page has the diagrams and screenshots the spec's Pages table lists for it
- [x] The job states in the state diagram are the ones `src/wambatic/reports/web.py` uses

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_docs.py` passes

**Notes:**

- Depends on Task 5

---

## Task 7: Write the guide pages on JSON and the metric groups

**Status:** done
**Priority:** high
**Complexity:** large
**Spec Reference:** Pages (`guide/json.md`, `guide/activity.md`, `guide/flow.md`, `guide/delivery.md`, `guide/popularity.md`)

**User Story:** As a user, I want each metric explained, with where its numbers come from, so that I can read a report without misreading it.

**Subtasks:**

- [x] `json.md`: an annotated example cut from a real `--format json` output of the docs cache (Material code annotations), the class diagram of its objects, and `jq` recipes. Check each recipe against that output
- [x] `activity.md`, from the README and the stats spec
- [x] `flow.md` with the pull-request timeline diagram
- [x] `delivery.md` with the deployment flowchart, the lead-time and failed-change timelines, and the delivery screenshots
- [x] `popularity.md` with the popularity and languages screenshots
- [x] Link each metric to its row in `reference/metrics.md`, and external terms as in Task 5

**Acceptance Criteria:**

- [x] Each page has the diagrams and screenshots the spec's Pages table lists for it
- [x] The JSON keys shown are those `wambatic.reports.base.result_to_dict` writes

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_docs.py` passes

**Notes:**

- Depends on Task 5
- The JSON example is cut down by hand from real output and labelled as cut. It is never invented

---

## Task 8: Write the cache, configuration, recipes, troubleshooting and limits pages

**Status:** done
**Priority:** medium
**Complexity:** medium
**Spec Reference:** Pages (`guide/cache.md`, `guide/config.md`, `guide/recipes.md`, `guide/troubleshooting.md`, `limits.md`); Drift test (images)

**User Story:** As a user, I want to know how the cache and config behave and what to do when something fails, so that I can fix problems myself.

**Subtasks:**

- [x] `cache.md` with the `cache info` screenshot and the sync-or-not flowchart
- [x] `config.md` with the layers flowchart and an annotated example
- [x] `recipes.md`:
  - the README's common workflows;
  - a nightly HTML report with `cron`, with a link to `crontab(5)`;
  - an offline report from the cache
- [x] `troubleshooting.md`: each one-line error message wambatic prints, found by searching `src/wambatic` for the error classes' messages, with what to do
- [x] `limits.md`: the README's limits, each with why
- [x] Add `test_images_exist` to `src/tests/test_docs.py`: every image path in `docs/**/*.md` resolves to a file, and every file under `docs/images/` is referenced. Run it once with an unreferenced image, and confirm it fails

**Acceptance Criteria:**

- [x] Each page has the diagrams and screenshots the spec's Pages table lists for it
- [x] `test_images_exist` passes, and fails on an unreferenced image

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_docs.py` passes

**Notes:**

- Depends on Task 5

---

## Task 9: Slim the README and point at the guide

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** Introduction (README); Implementation (README, AGENTS.md)

**Technical Goal:** One copy of each reference table, in the guide.

**Subtasks:**

- [x] Before deleting anything from the README, check that each section is covered in the guide: for each README section, name the guide page that holds its content, and add whatever is missing to that page
- [x] Cut `README.md` to:
  - the pitch;
  - Install;
  - The token, in two lines with a link;
  - A first report;
  - a "Documentation" link to <https://bnomis.github.io/wambatic/>;
  - More, and Updating the shared rules, unchanged apart from the guide link
- [x] Add `[project.urls]` with `Documentation` and `Repository` to `pyproject.toml`
- [x] Add to `AGENTS.md` that a change to user-visible behaviour (options, settings, defaults, output, errors) updates the guide in the same commit, and that `bin/screenshots.sh` is re-run when the output changes

**Acceptance Criteria:**

- [x] Every README section removed has its content in a named guide page, listed in the commit body
- [x] No table of options, settings or metrics remains in the README

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_package.py src/tests/test_docs.py` passes

**Notes:**

- Depends on Tasks 6, 7 and 8

---

## Task 10: Close the list

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** External dependencies (D2); all sections

**Technical Goal:** Every check passes on the whole tree before the branch merges, and the spec is marked done.

**Subtasks:**

- [ ] Run `bin/audit-check.sh`. If D2 flags `mkdocs` or `mkdocs-material` as declared but never imported, check `.agents/claude/skills/auditme/requests.md` for the open request "D2 should not flag dependencies that are only run as commands":
  - If it is still open, accept each hit with a scoped marker as the dev tools were (`accept[<rule>]`, with the reason "run as a command by the docs workflow, never imported").
  - If it has shipped and the hit persists, stop as `blocked` and give the hit.
- [ ] Add step 12, "User guide", to `agents/specs/implementation-order.md`, pointing at this task list, and mark step 11 done if it still says its tasks-2 is in progress (both audit task lists are merged)
- [ ] Set the spec's `**Status:**` to `implemented`
- [ ] Note in the final report that, after the first deploy, the operator sets the repository's Pages source to the `gh-pages` branch in the repository settings

**Acceptance Criteria:**

- [ ] Every check below passes on the whole tree
- [ ] The spec says `implemented`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `uv sync --group docs` succeeds
- [ ] `mkdocs build --strict` exits 0
- [ ] `pre-commit run --all-files` passes
- [ ] `pre-commit run --hook-stage pre-push --all-files` passes
- [ ] `pytest src/tests/test_docs.py src/tests/test_screenshots.py src/tests/test_package.py src/tests/test_cli.py src/tests/test_settings.py` passes
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 9
- The project has no affected-tests tool. No source module under `src/wambatic` changes in this list, so the tests above are the ones it can affect

---

---

## Task 11: Make the screenshot script write only the images the guide uses

**Status:** todo
**Priority:** low
**Complexity:** small
**Spec Reference:** Screenshots; Drift test (images)

**Technical Goal:** `bin/screenshots.sh` writes no image that no page references, so `test_images_exist` still passes after a re-run. Found in Task 8: the script writes the full set of terminal sections, crops and themes for both `repo:pallets/click` and `org:pallets`, and the guide uses a subset; the unreferenced files were deleted by hand.

**Subtasks:**

- [ ] Write only the images listed in a table in the script (or reference the extras from a page)
- [ ] Re-run the script and confirm `pytest src/tests/test_docs.py` and `src/tests/test_screenshots.py` pass

**Acceptance Criteria:**

- [ ] A re-run leaves `docs/images/` with no unreferenced file

**Definition of Done:**

- [ ] `mkdocs build --strict` exits 0
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 8
