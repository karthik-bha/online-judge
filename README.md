Markdown

# Judge

A Python evaluation and testing project.

## Project Setup

1. **Clone the repository:**
   ```bash
    git clone <your-repository-url>
    cd judge
   ```

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows (Command Prompt):
    .venv\Scripts\activate.bat
    # On Windows (PowerShell):
    .venv\Scripts\Activate.ps1
    ```
3. **Install the package and dependencies:**
    
    ```bash
    pip install -e .
    ```

4. **Running Tests & Linting**

    ***Run tests with Pytest:***
    ```bash
    pytest
    ```
    ***Run lint checks with Ruff:***
    ```bash
    ruff check .
    ```