# AI Agent Guide: How to use notebook_editor.py

This tool is designed for safe and reliable editing of Jupyter Notebook (.ipynb) files.
It operates without external dependencies and guarantees the preservation of the JSON structure.

## Core Workflow (Best Practice)

To make changes to the code, always follow this algorithm:

1. **Explore**: Get the list of cells to understand the structure.
    `python notebook_editor.py list <notebook.ipynb>`

2. **Read**: Export the content of the desired cell to a temporary file.
    `python notebook_editor.py read <notebook.ipynb> <cell_index> --to-file <temp_file.py>`

3. **Edit**: Read `<temp_file.py>`, make changes, and save them.

4. **Verify (Diff)**: (Optional) See what will change.
    `python notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

5. **Apply**: Update the cell from the file.
    `python notebook_editor.py update <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

### Inspecting Outputs

*   **View Results**: To see what your code printed or returned:
    `python notebook_editor.py read <notebook.ipynb> <cell_index> --include-output`

*   **Extract Images**: If you see `[BINARY DATA DETECTED]` in the output, save it to inspect:
    `python notebook_editor.py save-output <notebook.ipynb> <cell_index> --to-file image.png`

## Command Reference

### 1. View Structure (`list`)

Shows indices, cell types, and content preview (first 2 and last 2 lines of code, plus output summary).

```bash
python notebook_editor.py list my_notebook.ipynb --limit 50
```

### 2. Read Cell (`read`)

* **To Console** (for short cells):

    ```bash
    python notebook_editor.py read my_notebook.ipynb 5
    ```

* **To File** (RECOMMENDED for code):

    ```bash
    python notebook_editor.py read my_notebook.ipynb 5 --to-file cell_5.py
    ```

### 3. Search (`search`)

Finds cells containing text or regex (in source code and execution outputs).

```bash
python notebook_editor.py search my_notebook.ipynb "import pandas"
python notebook_editor.py search my_notebook.ipynb "def .*_handler" --regex
```

### 4. Update Cell (`update`)

Replaces the content of a cell. Automatically clears the cell output.

* **From File** (Safe):

    ```bash
    python notebook_editor.py update my_notebook.ipynb 5 --from-file updated_code.py
    ```

* **With Text** (Only for single lines):

    ```bash
    python notebook_editor.py update my_notebook.ipynb 5 --content "print('done')"
    ```

### 5. Add Cell (`add`)

Inserts a new cell before the specified index (or at the end if index=-1).

```bash
python notebook_editor.py add my_notebook.ipynb --index 0 --type markdown --content "# Title"
python notebook_editor.py add my_notebook.ipynb --type code --from-file new_script.py
```

### 6. Delete Cell (`delete`)

```bash
python notebook_editor.py delete my_notebook.ipynb 5
```

### 7. Preview Changes (`diff`)

Shows what will change before updating a cell.

```bash
python notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <file>
python notebook_editor.py diff <notebook.ipynb> <cell_index> --content "<text>"
```

### 8. Create Notebook (`create`)

Creates an empty valid .ipynb file.

```bash
python notebook_editor.py create new_notebook.ipynb
```
