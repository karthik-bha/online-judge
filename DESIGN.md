# Online Judge: Design Doc

Status: Draft v0.2

A coding practice platform (a LeetCode-style site). Users read a problem, write Python in a code editor, submit, and get a verdict from a judge that runs their code in a secure sandbox.

**Audience:** casual coders and recruiters looking at projects.

---

## 0. How this project is built

**Why:** to be able to build the core of a system end to end, without depending on AI for the hard parts.

**AI usage rules for this project**
- Allowed: learning concepts, discussing design tradeoffs, reviewing plans and documents.
- Allowed: AI-assisted boilerplate (configuration, scaffolding, CI and Docker files, basic model and endpoint skeletons).
- Not allowed: AI-written core logic. The sandbox runner, verdict engine, queue and worker logic (claiming, heartbeat, requeue), rate limiter, authentication logic, security fixtures, and validator logic are written by hand.
- A collaborator (a beginner friend) may use AI tools while learning. Their pull requests are reviewed, and they are quizzed on their code before merging.

This document was drafted with AI assistance from decisions I made, and reviewed by me. Update this section if the rules change, so any claim about the project stays accurate.

---

## 1. Goals

* Working coding platform with a login, code editor, problem set of 10, and judge
* Python as the only language
* Leaderboards
* User accounts: password reset (security question), profile view and edit
* Demo mode: try the platform without registering
* Code execution in a secure sandbox
* Syntax errors caught by the code editor (a convenience; the judge also checks)

## 2. Non-goals (not implemented)

* Multiple languages
* Contests
* Real-time updates (the frontend polls for verdicts)
* Email verification and any email service
* Custom checkers
* Admin panel (users, submissions, comments): next phase
* Profile pictures
* Discussions

---

## 3. Priorities

| Level | Contents |
|---|---|
| **P0** | Judge core works end to end for one problem: problem format, sandbox runner, verdict engine, fixtures, no login, no UI polish |
| **P1** | All 10 problems and a loader; API for problems and submissions; queue, workers, heartbeat, requeue; code editor page showing verdicts; IP-based rate limiting (anonymous use is the default until login exists) |
| **P2** | Registration and login (JWT), per-user rate limits, submission history, leaderboard, syntax-check endpoint, profile view |
| **P3** | Profile edit, security-question password reset, UI polish |
| **Ship** | Final adversarial pass, deployment on a VPS, documentation and demo polish |

If time runs short, cut from the bottom. The ship track can follow P1, P2, or P3.

---

## 4. Problem format

Defined in [docs/problem-spec.md](docs/problem-spec.md). In short:

* Each problem is a folder under `problems/` containing `problem.yaml`, `description.md`, `solution.py`, and `tests/`.
* Exactly 4 tests per problem: 2 visible, 2 hidden (one edge case and one extreme case).
* Test `N` uses `tests/0N.in` and `tests/0N.out`.
* Time and memory limits live only in `problem.yaml`.
* Input and output are stdin and stdout. Output is compared with trailing whitespace ignored and everything else exact.
* Every input has exactly one correct output (no custom checkers, no floating-point output).

---

## 5. Judge specification

### Verdicts
| Verdict | Meaning |
|---|---|
| Accepted | All test cases pass |
| Wrong Answer | Output differs from expected |
| Time Limit Exceeded | Ran longer than the problem's time limit |
| Memory Limit Exceeded | Used more than the problem's memory limit |
| Runtime Error | Program crashed or exited with an error |
| Compile Error | Syntax error (detected when Python starts or parses the code) |
| Output Limit Exceeded | Printed more than the output cap |
| Internal Error | The judge failed (not the user's fault) |

In-progress states: `queued`, `running`.

* The judge **stops at the first failing test**.
* For a failure on a hidden test, the user sees **only the verdict**, never the input or expected output.

### Limits (starting values; to be measured in the Level 1 spike)

| Setting | Starting value | Notes |
|---|---|---|
| Time limit | per problem, in `problem.yaml` | Wall-clock plus a CPU-time check |
| Memory limit | per problem, in `problem.yaml` | |
| Code size cap | 64 KB | Rejected at the API |
| Output cap | 1 MB | Beyond this: Output Limit Exceeded |
| Workers | 2 | One submission each at a time |
| Per-user submissions | 5 per minute | |
| Per-IP (anonymous demo) | 3 per minute | Stricter, no account |
| Global judging | about 10 per minute | Recompute: workers x 60 / seconds per submission |
| Queue cap | 50 | Beyond this: reject with "judge busy, try again" |
| Target time to verdict | 10 s typical | A goal to test against |

### If the judge is down
Return a "judge unavailable" error instead of queueing. See section 8 for how this is detected.

---

## 6. Architecture

```
Browser (React) -> API (FastAPI) -> Postgres
                       |
                     Queue (Postgres table) -> Worker -> Sandbox (Docker container)
```

* **API server:** takes requests and saves submissions. It never runs user code.
* **Database:** problems, test cases, submissions, results, users.
* **Queue and workers:** submissions wait in a Postgres-backed queue and hand-written worker processes judge them.
* **Sandbox:** a locked-down container, fully separate from the API server and its secrets.

### Life of a submission
1. The API saves the submission as `queued`.
2. A worker claims it and sets `running`.
3. For each test, the worker runs the code in a fresh sandbox with the test input and collects stdout, time, and memory.
4. The output is compared with the expected output and a verdict is chosen (stop at first failure).
5. The worker saves the verdict, and the frontend polls and shows it.

Sandbox start-up is kept behind one small function, `run(code, stdin, limits)`, so the execution backend can change later without touching the rest.

### Repository layout
```text
.github/workflows/   CI
docs/                documentation (problem-spec.md)
problems/            problem content, one folder per problem
src/judge/           sandbox runner and verdict engine (api/ and worker/ are added later)
tests/               pytest tests for the code
tools/               helper scripts
```

---

## 7. Tech stack

**Environment:** Windows PC with WSL2 (Ubuntu), Docker Desktop (WSL2 backend), VS Code. Sandbox work happens in WSL2. Git with `.gitattributes` to avoid line-ending problems.

**Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.0 + Alembic, PostgreSQL, pyjwt + argon2/bcrypt.

**Queue and workers:** Postgres queue (`SELECT ... FOR UPDATE SKIP LOCKED`), hand-written Python worker processes (no Celery).

**Sandbox:** Docker, controlled through the `docker` Python SDK.

**Frontend:** React, Vite, TypeScript, Monaco editor, TanStack Query, Tailwind.

**Tooling and CI:** pytest, ruff, optionally mypy, pre-commit, docker compose, GitHub Actions.

---

## 8. Sandbox, security, and workers

### Sandbox
Docker flags: `--network none`, `--memory`, `--cpus`, `--pids-limit`, `--read-only` with a size-capped `tmpfs`, `--cap-drop ALL`, `--security-opt no-new-privileges`, non-root user. Also enforced: wall-clock and CPU time limits, output cap, code size cap. A timeout must kill the container itself, not just stop waiting for it. Containers are labelled so leftovers can be found and removed.

**Security promise:** submitted code cannot read the host filesystem, use the network, or exhaust the host.

Notes:
* The worker host is dangerous because it can start containers. Keep database credentials and secrets off the machine that runs untrusted code where possible.
* Do not make the site public until the sandbox and rate limiting are done and attacked by me.
* Keep a log of "ways I tried to break my sandbox".

### Workers, heartbeat, and requeue
**Statuses:** `queued -> running -> done`, plus `internal_error`.

1. **Claiming:** a worker takes the oldest `queued` row atomically and records `status = running`, `worker_id`, and `started_at`.
2. **Heartbeat:** every ~5 s each worker writes a "last seen" timestamp.
3. **Judge-up check:** on submit, the API looks for any worker seen in the last ~15 s. If none, it returns "judge unavailable" and does not queue.
4. **Requeue (reaper):** every ~30 s, `running` rows whose worker has gone silent (or that exceed max job time plus a margin) go back to `queued` with `attempts + 1`.
5. **Poison submissions:** at `attempts = 3`, mark `internal_error`.
6. **Ownership check on save:** a worker saves its verdict only if the row is still `running` and assigned to it.
7. **Shutdown:** on a stop signal, a worker finishes its job or puts it back before exiting.

Test plan: kill a worker mid-judging and check the submission recovers.

---

## 9. Accounts, auth, and rate limiting

* **Auth:** JWT. Anonymous demo mode is available before and alongside login.
* **Rate limiting:** one limiter whose key comes from a single place: user id when logged in, IP address otherwise. Built first with IP (P1), then per user (P2). Behind a reverse proxy, client IPs must come from a trusted proxy configuration, not a blindly trusted `X-Forwarded-For` header.
* **Password reset:** security question, no email service. The user writes their own question; the answer is normalized and hashed like a password; attempts are rate-limited with lockout; unknown usernames get a plausible fake question; sessions are invalidated after a reset. Known weakness, accepted as a deliberate tradeoff: no email recovery.

## 10. Editor syntax check

`POST /check` takes code and returns line, column, and message, or OK. The editor calls it after a short pause in typing. It uses Python's `ast.parse`, which analyzes code without running it. Code size is capped and exceptions are caught. It is rate-limited separately and is a convenience only: the judge produces its own Compile Error verdict.

## 11. Rough data model

* `users` (including security question and hashed answer)
* `problems` (title, difficulty, time limit, memory limit)
* `test_cases` (problem, input, expected output, hidden flag)
* `submissions` (user or IP, problem, code, status, verdict, total time, attempts, worker_id, started_at)
* `submission_results` (per-test results)
* `workers` (worker_id, last_seen)

Submissions carry a nullable user reference from the start, so adding login later does not require reworking the model.

---

## 12. Hosting and deployment

* **Now:** run locally (WSL2 + Docker).
* **Later:** deploy on a VPS. Confirm the VPS supports Docker properly before buying. Vercel was considered, and Vercel Sandbox could be used as an alternative execution backend, but the plan is to build and learn on Docker first.
* **Before going public:** sandbox hardened and attacked, rate limits working (including the IP-based limit for demo users), worker host separated from database and secrets, usage or spending cap and a kill switch in place, README with screenshots and demo.
* Open question for a public repo: hidden tests and reference solutions are readable on GitHub. Decide whether that is acceptable or whether problem data is kept out of the public repo.

---

## 13. Roadmap

| Phase | Contents | Level |
|---|---|---|
| 1 | Repository and CI foundation | P0 |
| 2 | Problem specification and validator, sandbox spike and runner, verdict engine, verdict and security fixtures, container cleanup | P0 |
| 3 | Database, problem loader, walking skeleton (curl to verdict) | P1 |
| 4 | Submission and problem APIs, basic worker heartbeat | P1 |
| 5 | Worker reliability: requeue, ownership checks, graceful shutdown, structured logs | P1 |
| 6 | Backend integration check | P1 |
| 7 | Frontend | P1 |
| 8 | IP rate limiting and the P1 gate (all 10 problems valid) | P1 |
| 9 | Authentication | P2 |
| 10 | User features: history, profile, leaderboard, syntax check | P2 |
| 11 | Profile edit and password reset | P3 |
| Ship | Adversarial pass, deployment, documentation | any |

Tests grow with each phase. Security and failure tests are added alongside the code they test, and the final adversarial pass repeats them with fresh eyes.

---

## 14. Collaboration and CI

* A friend (beginner) takes easy parts: problem content, the loader script, frontend pages against a fake API, a stats endpoint, fixture solutions, and documentation.
* I keep the sandbox, queue and workers, authentication, rate limiting, and anything security-related.
* The problem format and API shapes are agreed first. Work happens on branches with pull requests.
* **CI on every PR and push (GitHub Actions):** lint (`ruff`), unit tests (`pytest`), problem validator, judge self-test against fixture solutions, sandbox-escape tests, Docker build check. Branch protection is applied where the GitHub plan allows it.

---

## 15. Definition of done for v1 (draft)

A new user can register, solve a problem, and see Accepted; all fixture solutions get the right verdicts; all sandbox-escape attempts fail; the killed-worker test recovers; and the README lets a stranger run the project.

---

## 16. Open items

* Measure real numbers in the Level 1 spike (container start-up time, timeout behavior, memory-kill behavior) and update the limits table.
* Write a verdict detection table before coding the verdict engine: how each verdict is recognized (for example, MLE from the container's out-of-memory flag, TLE from the judge's own timeout flag), and which verdict wins when several apply.
* Decide whether the public repo contains hidden tests and reference solutions.
* Decide the leaderboard ranking rule before Phase 10.
* Choose the VPS provider and plan when deployment gets closer.