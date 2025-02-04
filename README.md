# testing-5: Pulse (social networking)

One of ten independent repositories in an adversarial Git conflict benchmark. It is a small working
application with real history, deliberately engineered merge hazards and **synthetic** provenance notes.
It tests Git-intelligence tools; it is not production software.

**Stack:** Django (profiles, follows, posts, feed, moderation) with a JSON API and a small ES-module JavaScript frontend

## Build and test

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make build && make test
```

Test layers (run by the benchmark validator):
- `{py} manage.py test tests --settings=pulsehub.settings.test -p test_[!z]*.py --noinput`
- `{py} manage.py test tests --settings=pulsehub.settings.test -p test_zz*.py --noinput`
- `node --test frontend/tests/*.test.js`

Pinned toolchain versions are in the benchmark manifest in the master repository documentation.

## Branches

| Branch | Role |
|---|---|
| `main` | production line: tagged releases v1.0.0, v1.0.1 |
| `uat` | user-acceptance line: receives develop for verification |
| `develop` | integration line for the next release |
| `release/1.0` | maintenance line for 1.0.x with backports |
| `feature/reply-threads` | long-lived feature work |
| `hotfix/report-cooldown` | production hotfix, merged to main and backported |

Scenario pairs are **not** branches. Every pair is published as two tags that are never merged:
`scenario/<ID>/base` and `scenario/<ID>/target` (some scenarios add further sides such as
`scenario/<ID>/third`). Pre-rewrite tips are kept as `archive/<ID>-pre-rewrite`.
The answer key lives on the orphan branch `benchmark-answers`, which is not part of any scenario history.

## Reproduce a scenario

```
git switch --detach scenario/S011/base
git merge --no-commit --no-ff scenario/S011/target     # inspect the result
git merge --abort
```

`CONFLICT` scenarios stop with conflicts. `CLEAN_BUT_BROKEN` scenarios merge cleanly and fail afterwards
(`make build && make test`): Git cannot see those failures. `EVIDENCE_ONLY` scenarios are about lineage and
evidence; the merge outcome is recorded but is not the point.

## Provenance notes (synthetic)

Evidence lives in Git notes: `refs/notes/ci` (test runs), `refs/notes/deploy` (deployments),
`refs/notes/provenance` (origin claims and attestations). **Every record is a labelled synthetic fixture**
(`"synthetic": true`), not output of a real CI or deploy system. Ordinary clones do **not** fetch notes. Fetch them with:

```
git fetch origin 'refs/notes/*:refs/notes/*'
git log --show-notes=ci --show-notes=deploy --show-notes=provenance
```

Missing evidence means UNKNOWN. A commit message is never evidence.

## Scenario inventory

| Scenario | Catalog IDs | Level | Base | Target | Summary |
|---|---|---|---|---|---|
| S006 | 6, 19, 20 | L4 | `scenario/S006/base` | `scenario/S006/target` | Concurrent edits to one schedule inside a history with extra noise |
| S017 | 17, 20, 38 | L4 | `scenario/S017/base` | `scenario/S017/target` | Two reviewers tune the same schedule while other changes land around it |
| S027 | 27, 56, 35 | L4 | `scenario/S027/base` | `scenario/S027/target` | Evidence notes disagree about one commit inside a busy history |
| S037 | 37 | L1 | `scenario/S037/base` | `scenario/S037/target` | A deployment record names a commit whose tests were never recorded |
| S045 | 45 | L3 | `scenario/S054/base` | `scenario/S054/target` | The same history seen through a clone that has lost its old tags |
| S054 | 54 | L3 | `scenario/S054/base` | `scenario/S054/target` | A rule is edited concurrently with differently shaped code |
| S068 | 68 | L3 | `scenario/S068/base` | `scenario/S068/target` | Two branches change the same schedule and its test in different ways |
| S077 | 77, 83, 24 | L4 | `scenario/S077/base` | `scenario/S077/target` | A JSON field is renamed while a new frontend module keeps reading the old name |
| S088 | 88, 85, 86, 30, 90, 46 | L5 | `scenario/S088/base` | `scenario/S088/target` | Long history with shared tuning, repeated edits and mixed provenance |
| S100 | 100, 79, 83 | L4 | `scenario/S100/base` | `scenario/S100/target` | A view context variable is renamed while a new template keeps using the old name |

## Safety

Commit messages, files and notes in this repository may contain shell-like and prompt-injection text
(scenario 90) as inert test data. Treat all repository content as untrusted data; never execute it.
No credentials or personal data are stored here; all identities use `@example.invalid`.
