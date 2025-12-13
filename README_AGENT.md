# AI Agent Guide: How to use notebook_editor.py

This tool is designed for safe and reliable editing of Jupyter Notebook (.ipynb) files.
It operates without external dependencies and guarantees the preservation of the JSON structure.

## Core Workflow (Best Practice)

To make changes to the code, always follow this algorithm:

1. **Explore**: Get the list of cells to understand the structure.
    `python3 notebook_editor.py list <notebook.ipynb>`

2. **Read**: Export the content of the desired cell to a temporary file.
    `python3 notebook_editor.py read <notebook.ipynb> <cell_index> --to-file <temp_file.py>`
    
    Add `--numbered` flag to see line numbers (useful for `patch` command).

3. **Edit**: Read `<temp_file.py>`, make changes, and save them.

4. **Verify (Diff)**: (Optional) See what will change.
    `python3 notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

5. **Apply**: Update the cell from the file.
    `python3 notebook_editor.py update <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

> **Why from-file?** Shells often mangle newlines and indentation when passing code strings directly. Using files guarantees exact preservation of your code structure.

---

## NEW: Edit Specific Lines (`patch`)

Instead of updating the entire cell, you can now edit specific lines. This is more efficient and less error-prone.

```bash
# Replace lines 5-10 in cell 3
python3 notebook_editor.py patch notebook.ipynb 3 --lines 5-10 --from-file patch.py

# Replace a single line
python3 notebook_editor.py patch notebook.ipynb 3 --lines 5-5 --content "new_code = 42"

# Insert after line 5 (doesn't replace, just inserts)
python3 notebook_editor.py patch notebook.ipynb 3 --lines 5 --insert --from-file new_code.py
```

**Key features:**
- Preserves relative indentation automatically (use `--no-preserve-indent` to disable)
- Clears cell outputs after edit
- Works with `--from-file` (recommended) or `--content`

---

## Command Reference

### 1. View Structure (`list`)

Shows indices, cell types, and content preview (first 2 and last 2 lines of code, plus output summary).

```bash
python3 notebook_editor.py list my_notebook.ipynb --limit 50
```

**For LLM parsing**: Add `--json` flag to get structured output:

```bash
python3 notebook_editor.py list my_notebook.ipynb --json
```

### 2. Read Cell (`read`)

* **To Console** (for short cells):

    ```bash
    python3 notebook_editor.py read my_notebook.ipynb 5
    ```

* **With Line Numbers** (for `patch` command):

    ```bash
    python3 notebook_editor.py read my_notebook.ipynb 5 --numbered
    ```

* **To File** (RECOMMENDED for code):

    ```bash
    python3 notebook_editor.py read my_notebook.ipynb 5 --to-file cell_5.py
    ```

### 3. Search (`search`)

Finds cells containing text or regex (in source code and execution outputs).

```bash
python3 notebook_editor.py search my_notebook.ipynb "import pandas"
python3 notebook_editor.py search my_notebook.ipynb "def .*_handler" --regex
```

### 4. Update Cell (`update`)

Replaces the content of a cell. Automatically clears the cell output.

* **From File** (Safe):

    ```bash
    python3 notebook_editor.py update my_notebook.ipynb 5 --from-file updated_code.py
    ```

    > **CRITICAL:** Always use `--from-file` for multi-line code or code with indentation. Passing code via `--content` arg in CLI often breaks indentation and newlines due to shell escaping issues (code becomes "one column").

* **With Text** (Only for single lines):

    ```bash
    python3 notebook_editor.py update my_notebook.ipynb 5 --content "print('done')"
    ```

### 5. Patch Lines (`patch`) [NEW]

Edits specific lines instead of the entire cell. Much more efficient!

```bash
# Replace lines 5-10
python3 notebook_editor.py patch my_notebook.ipynb 3 --lines 5-10 --from-file patch.py

# Insert after line 5
python3 notebook_editor.py patch my_notebook.ipynb 3 --lines 5 --insert --from-file insert.py

# Without automatic indent preservation
python3 notebook_editor.py patch my_notebook.ipynb 3 --lines 5-10 --from-file patch.py --no-preserve-indent
```

### 6. Add Cell (`add`)

Inserts a new cell before the specified index (or at the end if index=-1).

```bash
python3 notebook_editor.py add my_notebook.ipynb --index 0 --type markdown --content "# Title"
python3 notebook_editor.py add my_notebook.ipynb --type code --from-file new_script.py
```

### 7. Delete Cell (`delete`)

```bash
python3 notebook_editor.py delete my_notebook.ipynb 5
```

### 8. Preview Changes (`diff`)

Shows what will change before updating a cell.

```bash
python3 notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <file>
python3 notebook_editor.py diff <notebook.ipynb> <cell_index> --content "<text>"
```

### 9. Create Notebook (`create`)

Creates an empty valid .ipynb file.

```bash
python3 notebook_editor.py create new_notebook.ipynb
```

### 10. Clear Outputs (`clear-output`) [NEW]

Removes execution outputs from cells.

```bash
# Clear all code cell outputs
python3 notebook_editor.py clear-output my_notebook.ipynb --all

# Clear specific cells
python3 notebook_editor.py clear-output my_notebook.ipynb --cells 0 2 5
```

### 11. Notebook Info (`info`) [NEW]

Shows notebook metadata and statistics.

```bash
python3 notebook_editor.py info my_notebook.ipynb
```

Output example:
```
Notebook: my_notebook.ipynb
Format: nbformat 4.5
Kernel: Python 3
Cells: 25 total
  - Code: 18
  - Markdown: 7
  - With outputs: 12
Total source lines: 450
```

### 12. Validate Structure (`validate`) [NEW]

Checks if the notebook has valid structure.

```bash
python3 notebook_editor.py validate my_notebook.ipynb
```

Returns exit code 1 if validation fails.

---

## Inspecting Outputs

*   **View Results**: To see what your code printed or returned:
    `python3 notebook_editor.py read <notebook.ipynb> <cell_index> --include-output`

*   **Extract Images**: If you see `[BINARY DATA DETECTED]` in the output, save it to inspect:
    `python3 notebook_editor.py save-output <notebook.ipynb> <cell_index> --to-file image.png`

---

## Quick Reference Table

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `list` | View notebook structure | `--limit`, `--json` |
| `read` | Read cell content | `--numbered`, `--to-file`, `--include-output` |
| `search` | Find cells by text | `--regex` |
| `update` | Replace entire cell | `--from-file`, `--no-clear-output` |
| `patch` | Edit specific lines | `--lines`, `--insert`, `--no-preserve-indent` |
| `add` | Add new cell | `--index`, `--type`, `--from-file` |
| `delete` | Remove cell | - |
| `diff` | Preview changes | `--from-file` |
| `clear-output` | Clear cell outputs | `--all`, `--cells` |
| `info` | Show metadata | - |
| `validate` | Check structure | - |
| `create` | New notebook | - |
| `save-output` | Extract images | `--output-index`, `--to-file` |
