from pathlib import Path

import yaml


# file path would also contain the name of folder of problem
def validate_problem(problem_path: Path)-> list[str]:

    errors=[]

    # check if problem has required top files
    required_files= ["description.md", "problem.yaml", "solution.py"]
    for file_name in required_files:
        if not (problem_path / file_name).is_file():
            errors.append(f"Missing required file: {file_name}")
            

    # check if tests directory exists
    tests_dir= problem_path / "tests"
    if not tests_dir.is_dir():
        errors.append("Missing required directory: tests/")
        return errors

    # parse problem.yaml
    yaml_path= problem_path / "problem.yaml"
    
    if yaml_path.is_file():
        try:
            with open(yaml_path, "r") as f:
                data= yaml.safe_load(f)
                if data is None:
                    errors.append("YAML file is empty, please write problem specification")
                    return errors
                if type(data) is not dict:
                    errors.append("YAML file is not in proper format")
                    return errors
        
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax in problem.yaml: {e}")
            return errors

        # check if problem_id name matches the actual folder name
        problem_id= data.get("id")
        if problem_id != problem_path.name:
            errors.append(f"Folder name '{problem_path.name}' does not match problem.yaml id '{problem_id}'")
            
        # check test case structure and counts 
        tests = data.get("tests")

        if tests is None:
            errors.append("Missing required field 'tests' in problem.yaml")
            return errors
        if not isinstance(tests, list):
            errors.append("'tests' field must be a list")
            return errors

        if len(tests) != 4:
            errors.append(f"Problem must have exactly 4 tests, found {len(tests)}")
             
        visible_count = 0
        invisible_count = 0

        for idx, t in enumerate(tests):
            if not isinstance(t, dict):
                errors.append(f"Test item at index {idx} must be a mapping (dictionary), got {type(t).__name__}")
                continue
                
            if t.get("hidden") is False:
                visible_count += 1
            elif t.get("hidden") is True:
                invisible_count += 1

        if visible_count != 2 or invisible_count != 2:
            errors.append(f"Problem must have exactly 2 visible and 2 invisible, found {visible_count} visible and {invisible_count} invisible cases")
    
    return errors