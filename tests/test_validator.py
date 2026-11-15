from pathlib import Path

import yaml

from tools.validate_problem import validate_problem


def create_valid_problem(problem_dir: Path):
    # create a valid problem for testing , passed problem_dir has problem name as well

    # create folder
    problem_dir.mkdir(parents=True, exist_ok=True)

    #create problem.yaml
    yaml_content= {
        "id": problem_dir.name,
        "title": "Test Problem",
        "difficulty": "easy",
        "time_limit_ms": 2000,
        "memory_limit_mb": 128,
        "tests": [
            {"id": 1, "hidden": False},
            {"id": 2, "hidden": False},
            {"id": 3, "hidden": True},
            {"id": 4, "hidden": True},
        ]
    }

    with open(problem_dir/"problem.yaml","w") as f:
        yaml.dump(yaml_content,f)

    # create description
    (problem_dir / "description.md").write_text("# Test Description")

    # create solution file
    (problem_dir / "solution.py").write_text("print('hello')")

    # create test dir
    tests_dir = problem_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # create test files
    for i in range(1,5):
        (tests_dir/f"{str(i).zfill(2)}.in").write_text(f"input {i}")
        (tests_dir / f"{str(i).zfill(2)}.out").write_text(f"output {i}")

    
def test_valid_problem(tmp_path):
    # completely valid, expect no errors 
    p_dir= tmp_path / "sum-of-list"
    create_valid_problem(p_dir)

    errors= validate_problem(p_dir)
    assert errors == []

def test_missing_fields(tmp_path):
    # missing files description and solution must be flagged 
    p_dir= tmp_path / "sum-of-list"
    p_dir.mkdir()

    # make only problem.yaml, omit everything else
    (p_dir / "problem.yaml").write_text("id: sum-of-list")

    errors= validate_problem(p_dir)
    assert any("Missing required file: description.md" in e for e in errors)
    assert any("Missing required file: solution.py" in e for e in errors)

def test_empty_yaml(tmp_path):
    # test if empty yaml is flagged
    p_dir= tmp_path / "sum-of-list"
    p_dir.mkdir()
    (p_dir / "problem.yaml").write_text("")
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
   
    errors= validate_problem(p_dir)
    assert any("file is empty" in e for e in errors)

def test_invalid_yaml_format(tmp_path):
    # test bad yaml format
    p_dir= tmp_path / "sum-of-list"
    p_dir.mkdir()
    (p_dir / "problem.yaml").write_text("hello")
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
   
    errors= validate_problem(p_dir)
    assert any("file is not in proper format" in e for e in errors)   

def test_folder_id_mismatch(tmp_path):
    # folder name and id in problem mismatch must be flagged 
    p_dir= tmp_path / "wrong-file-name"
    create_valid_problem(p_dir)

    yaml_content = {
        "id": "sum-of-list",
        "tests": [{"id": 1, "hidden": False}]
    }
    with open(p_dir / "problem.yaml", "w") as f:
        yaml.dump(yaml_content, f)

    errors = validate_problem(p_dir)
    assert any("does not match problem.yaml id" in e for e in errors)


def test_insufficient_tests(tmp_path):
    # problems should have exactly 4 test cases. 2 visible and 2 invisible
    p_dir = tmp_path / "sum-of-list"
    p_dir.mkdir()
    
    yaml_content = {
        "id": "sum-of-list",
        "tests": [
            {"id": 1, "hidden": False},
            {"id": 2, "hidden": True}
        ]
    }
    with open(p_dir / "problem.yaml", "w") as f:
        yaml.dump(yaml_content, f)
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
    
    errors = validate_problem(p_dir)
    assert any("must have exactly 4 tests" in e for e in errors)
    assert any("must have exactly 2 visible and 2 invisible" in e for e in errors)

def test_missing_tests_field(tmp_path):
    """Missing 'tests' key in problem.yaml should be caught and reported as an error."""
    p_dir = tmp_path / "sum-of-list"
    p_dir.mkdir()
    
    yaml_content = {
        "id": "sum-of-list",
        "title": "Test Problem",
        "time_limit_ms": 2000,
        "memory_limit_mb": 128
        # 'tests' field is completely missing
    }
    with open(p_dir / "problem.yaml", "w") as f:
        yaml.dump(yaml_content, f)
        
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
    
    errors = validate_problem(p_dir)
    assert any("Missing required field 'tests'" in e for e in errors)


def test_tests_is_not_a_list(tmp_path):
    # If 'tests' is provided as a non-list type (e.g., an integer), it should fail gracefully.
    p_dir = tmp_path / "sum-of-list"
    p_dir.mkdir()
    
    yaml_content = {
        "id": "sum-of-list",
        "tests": 12345  # Invalid type: integer instead of list
    }
    with open(p_dir / "problem.yaml", "w") as f:
        yaml.dump(yaml_content, f)
        
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
    
    errors = validate_problem(p_dir)
    assert any("must be a list" in e for e in errors)


def test_tests_items_are_not_mappings(tmp_path):
    # If items inside the 'tests' list are primitive types (like numbers), it should be reported.
    p_dir = tmp_path / "sum-of-list"
    p_dir.mkdir()
    
    yaml_content = {
        "id": "sum-of-list",
        "tests": [1, 2, 3, 4]  # List of integers instead of dictionaries/mappings
    }
    with open(p_dir / "problem.yaml", "w") as f:
        yaml.dump(yaml_content, f)
        
    (p_dir / "description.md").write_text("desc")
    (p_dir / "solution.py").write_text("sol")
    (p_dir / "tests").mkdir()
    
    errors = validate_problem(p_dir)
    assert any("must be a mapping" in e for e in errors)

