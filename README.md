# Online Judge

A coding practice platform in the style of LeetCode. Users read a problem, write Python in a code editor, submit it, and get a verdict from a judge that runs the code inside a locked-down sandbox.

> **Status: early development.** The problem format is defined and the judge core is being built. There is no runnable application yet, and nothing here is deployed.

## Planned features

- Python submissions judged in a secure Docker sandbox
- 10 problems, each with 2 visible and 2 hidden test cases
- Verdicts: Accepted, Wrong Answer, Time Limit Exceeded, Memory Limit Exceeded, Runtime Error, Compile Error, Output Limit Exceeded, Internal Error
- Code editor with syntax checking
- Queue and workers that survive crashes (heartbeat, requeue, poison-submission handling)
- Rate limiting, anonymous demo mode, then accounts, submission history, and a leaderboard

Not planned for the first version: multiple languages, contests, real-time updates, email features, custom checkers, an admin panel.

## Tech stack

Python, FastAPI, PostgreSQL, SQLAlchemy and Alembic, Docker (sandbox), React with Vite and TypeScript, pytest and ruff, GitHub Actions.

## Repository layout

```text
.github/workflows/   CI pipeline
docs/                Documentation, including the problem specification
problems/            Problem content (one folder per problem)
src/                 Application code (src/judge holds the sandbox and verdict engine)
tests/               Automated tests for the code
tools/               Helper scripts
DESIGN.md            Design document: goals, architecture, decisions
```

## Documentation

- [DESIGN.md](DESIGN.md): goals, architecture, decisions, and open questions
- [docs/problem-spec.md](docs/problem-spec.md): how to write a valid problem

## Getting started

> Adjust these commands to match `pyproject.toml` once the dependencies are finalized.

```bash
# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1

# install the project and its development tools
pip install -e ".[dev]"

# run the checks
ruff check .
pytest
```

The sandbox needs Docker. Development of the sandbox happens on Linux (WSL2 on Windows).

## Contributing

- Work on a branch and open a pull request. CI (lint and tests) must pass before merging.
- New problems must follow [docs/problem-spec.md](docs/problem-spec.md).
- Changes to the sandbox, workers, or authentication code get a closer review.

## License

To be decided.