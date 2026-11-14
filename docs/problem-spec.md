# Problem specification

This document defines how to write a valid problem for the judge. Rules marked **(validator)** are checked automatically by the problem validator. The rest are checked by a human before a problem is merged.

## 1. Folder layout

Every problem lives in its own folder under `problems/`. The folder name must equal the problem `id`.

```text
problems/
└── sum-of-list/
    ├── problem.yaml
    ├── description.md
    ├── solution.py
    └── tests/
        ├── 01.in
        ├── 01.out
        ├── 02.in
        ├── 02.out
        ├── 03.in
        ├── 03.out
        ├── 04.in
        └── 04.out
```

- All four items (`problem.yaml`, `description.md`, `solution.py`, `tests/`) are required. **(validator)**
- The problem `id` must be unique across all problems. **(validator)**

## 2. problem.yaml

```yaml
id: sum-of-list
title: Add a list of numbers
difficulty: easy
time_limit_ms: 2000
memory_limit_mb: 128

tests:
  - id: 1
    hidden: false
  - id: 2
    hidden: false
  - id: 3
    hidden: true
  - id: 4
    hidden: true
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Lowercase letters, digits and hyphens only. Must match the folder name. |
| `title` | string | yes | Shown on the problem list page. |
| `difficulty` | string | yes | One of `easy`, `medium`, `hard`. |
| `time_limit_ms` | integer | yes | Time limit in milliseconds. Must be greater than 0. |
| `memory_limit_mb` | integer | yes | Memory limit in megabytes. Must be greater than 0. |
| `tests` | list | yes | Exactly 4 entries (see sections 3 and 5). |

- Each entry in `tests` has an integer `id` and a boolean `hidden`.
- Test ids must be 1, 2, 3, 4 with no gaps or duplicates.
- The file must be valid YAML. **(validator)**

## 3. Test files

- A test with id `N` uses the files `tests/0N.in` and `tests/0N.out` (ids are zero-padded to two digits, e.g. id 1 means `01.in` and `01.out`).
- The yaml only **lists** the tests. The judge works out the file names from the test ids using this rule.
- Every listed test must have both files, and `tests/` must contain no other files. **(validator)**
- `.in` holds exactly what the program receives on stdin. `.out` holds exactly what the correct program prints.
- No labels, messages or comments inside either file.
- Plain UTF-8 text with LF line endings. Each file ends with a single newline.

## 4. Input and output conventions

**Input**
- The `.in` file is the program's stdin, byte for byte. The layout (for example, a single line of space-separated integers) is defined in `description.md`, and the description, example and `.in` files must all agree.
- Input values may be integers, floats or strings.

**Output**
- The judge compares the program's stdout with the `.out` file. Trailing whitespace on each line and trailing blank lines are ignored. Everything else must match exactly, including case.
- There are no custom checkers, so **every input must have exactly one correct output.** A problem with several valid answers is not allowed unless the description defines a single canonical form (for example, "print indices in ascending order").
- Outputs must be integers or strings. Do not use floating-point output.

## 4a. description.md

The description must contain these parts: problem statement, input format, output format, an example, and constraints. **(validator: checks the headings exist)**

- Constraints must give a range for every input value (for example `1<=n<=100`).
- The description must **not** state the time or memory limit (see section 6). **(validator)**
- The example must be identical to one visible test.

## 5. Tests per problem

- Exactly 4 tests: 2 visible (`hidden: false`) and 2 hidden (`hidden: true`). **(validator)**
- At least one visible test must be the example shown in the description.
- The two hidden tests are one **edge case** (for example, a minimum-size or unusual input) and one **extreme case** (near the maximum constraints).
- Avoid similar-looking tests and aim for variety.
- Every test input must respect the constraints in the description.

## 6. Limits

- Time and memory limits are specified in `problem.yaml` only.
- Do not repeat them in `description.md`. The website displays them from the yaml.

## 7. Reference solution

- Every problem must have a `solution.py` that reads stdin and prints only the answer (no prompts such as `input("Enter: ")`).
- It must be robust and finish within the problem's limits.
- CI runs `solution.py` through the judge and expects **Accepted** on all four tests. **(validator / CI)**

## 8. Checklist before submitting a problem

Checked automatically:
- [ ] Folder name equals the `id`, and the id format is valid
- [ ] `problem.yaml` parses and all required fields are present with valid values
- [ ] Exactly 4 tests: 2 visible, 2 hidden, ids 1 to 4
- [ ] Every listed test has a `.in` and `.out`, and there are no extra files
- [ ] The description has all required parts and no time or memory limits
- [ ] The reference solution gets Accepted on all four tests

Checked by a human:
- [ ] No typos; input and output formats are stated clearly
- [ ] The description's example is identical to a visible test
- [ ] Constraints exist for every input value, and every test respects them
- [ ] The hidden tests are one edge case and one extreme case
- [ ] The answer to every input is unique (no several-valid-answers problem)