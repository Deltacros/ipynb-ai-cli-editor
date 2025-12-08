# Jupyter Notebook Editor for AI Agents

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)](https://github.com/yourusername/notebook-editor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **zero-dependency**, **AI-agent-friendly** command-line tool for programmatically editing Jupyter Notebook (`.ipynb`) files. Designed specifically for Large Language Models (LLMs) and automated workflows.

[Русская версия](README_RU.md) | [English](README.md)

---

## 🎯 Why This Tool?

Traditional Jupyter notebook editing requires either:

- A full Jupyter environment with heavy dependencies
- Manual JSON manipulation (error-prone and fragile)
- Complex libraries that may not work in restricted environments

**This tool solves these problems** by providing:

✅ **Zero Dependencies** - Uses only Python standard library  
✅ **AI-Agent Optimized** - Clear CLI interface with file-based I/O pattern  
✅ **JSON-Safe** - Preserves notebook structure and metadata  
✅ **Portable** - Works anywhere Python 3.6+ is installed  
✅ **Reliable** - Predictable behavior for automated workflows  

---

## 🚀 Quick Start

### Installation

No installation needed! Just download the script:

```bash
wget https://raw.githubusercontent.com/yourusername/notebook-editor/main/notebook_editor.py
chmod +x notebook_editor.py
```

Or clone the repository:

```bash
git clone https://github.com/yourusername/notebook-editor.git
cd notebook-editor
```

### Basic Usage

```bash
# List all cells in a notebook
python notebook_editor.py list my_notebook.ipynb

# Read a specific cell
python notebook_editor.py read my_notebook.ipynb 5 --to-file cell_content.py

# Update a cell from file
python notebook_editor.py update my_notebook.ipynb 5 --from-file modified_content.py

# Search for content
python notebook_editor.py search my_notebook.ipynb "import pandas"

# Add a new cell
python notebook_editor.py add my_notebook.ipynb --type code --from-file new_code.py

# Delete a cell
python notebook_editor.py delete my_notebook.ipynb 5
```

---

## 📖 Complete Command Reference

### 1. **list** - View Notebook Structure

Shows all cells with their indices, types, and content preview.

```bash
python notebook_editor.py list <notebook.ipynb> [--limit N]
```

**Example:**

```bash
python notebook_editor.py list analysis.ipynb --limit 20
```

**Output:**

```
Total cells: 15
[0] CODE: import pandas as pd
[1] CODE: df = pd.read_csv('data.csv')
[2] MARKDOWN: ## Data Analysis
...
```

---

### 2. **read** - Extract Cell Content

Read a specific cell's content to console or file.

```bash
python notebook_editor.py read <notebook.ipynb> <cell_index> [--to-file <output_file>]
```

**Examples:**

```bash
# Print to console
python notebook_editor.py read analysis.ipynb 5

# Print with execution outputs (text and image placeholders)
python notebook_editor.py read analysis.ipynb 5 --include-output

# Save to file (RECOMMENDED for code editing)
python notebook_editor.py read analysis.ipynb 5 --to-file cell_5.py
```

---

### 3. **search** - Find Content

Search for text or regex patterns across all cells.

```bash
python notebook_editor.py search <notebook.ipynb> "<query>" [--regex]
```

**Examples:**

```bash
# Simple text search
python notebook_editor.py search analysis.ipynb "import pandas"

# Regex search
python notebook_editor.py search analysis.ipynb "def .*_handler" --regex
```

**Output:**

```
Match in Cell [3] (code):
  > import pandas as pd
Match in Cell [7] (code):
  > df = pandas.DataFrame()
Found matches in 2 cells: [3, 7]
```

---

### 4. **update** - Modify Cell Content

Replace the content of an existing cell. Automatically clears cell outputs.

```bash
python notebook_editor.py update <notebook.ipynb> <cell_index> --from-file <file>
python notebook_editor.py update <notebook.ipynb> <cell_index> --content "<text>"
```

**Examples:**

```bash
# Update from file (RECOMMENDED)
python notebook_editor.py update analysis.ipynb 5 --from-file modified_code.py

# Update with inline text (for simple changes)
python notebook_editor.py update analysis.ipynb 5 --content "print('Hello World')"

# Keep outputs (don't clear)
python notebook_editor.py update analysis.ipynb 5 --from-file code.py --no-clear-output
```

---

### 5. **add** - Insert New Cell

Add a new code or markdown cell at a specific position.

```bash
python notebook_editor.py add <notebook.ipynb> --type <code|markdown> --from-file <file>
python notebook_editor.py add <notebook.ipynb> --type <code|markdown> --content "<text>"
```

**Examples:**

```bash
# Add at the beginning
python notebook_editor.py add analysis.ipynb --index 0 --type markdown --content "# Introduction"

# Add at the end (default)
python notebook_editor.py add analysis.ipynb --type code --from-file new_analysis.py

# Insert at specific position
python notebook_editor.py add analysis.ipynb --index 5 --type code --content "print('checkpoint')"
```

---

### 6. **delete** - Remove Cell

Delete a cell by its index.

```bash
python notebook_editor.py delete <notebook.ipynb> <cell_index>
```

**Example:**

```bash
python notebook_editor.py delete analysis.ipynb 5
```

---

### 7. **diff** - Preview Changes

Show what will change before updating a cell.

```bash
python notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <file>
python notebook_editor.py diff <notebook.ipynb> <cell_index> --content "<text>"
```

**Example:**

```bash
python notebook_editor.py diff analysis.ipynb 5 --from-file modified_code.py
```

**Output:**

```diff
--- Cell 5 (Current)
+++ New Content
@@ -1,3 +1,4 @@
 import pandas as pd
-df = pd.read_csv('old_data.csv')
+df = pd.read_csv('new_data.csv')
+df = df.dropna()
```

---

### 8. **create** - New Notebook

Create a new empty notebook with valid structure.

```bash
python notebook_editor.py create <notebook.ipynb>
```

**Example:**

```bash
python notebook_editor.py create new_analysis.ipynb
```

---

### 9. **save-output** - Extract Images/Binary Data

Extracts binary data (like images) from a cell's output to a file.

```bash
python notebook_editor.py save-output <notebook.ipynb> <cell_index> --to-file <output_file> [--output-index N]
```

**Example:**

```bash
# Save the plot from cell 5 to an image file
python notebook_editor.py save-output analysis.ipynb 5 --to-file plot.png
```

**Output:**
```
Saved image/png data from Cell 5, Output 0 to 'plot.png'.
```

---

## 🤖 Best Practice Workflow for AI Agents

> **Note for Users:** There is a dedicated guide for AI agents located at [`README_AGENT.md`](README_AGENT.md). Please provide this file to your AI agent to help it understand how to use this tool effectively.

When modifying notebook code, follow this **file exchange pattern**:

```bash
# 1. Explore: Understand the notebook structure
python notebook_editor.py list notebook.ipynb

# 2. Extract: Export cell content to a temporary file
python notebook_editor.py read notebook.ipynb 5 --to-file temp_cell.py

# 3. Edit: Read temp_file.py, make changes, save modifications
# (AI agent or human edits temp_cell.py here)

# 4. Preview: (Optional) Check what will change
python notebook_editor.py diff notebook.ipynb 5 --from-file temp_cell.py

# 5. Apply: Update the cell from the modified file
python notebook_editor.py update notebook.ipynb 5 --from-file temp_cell.py
```

### Why This Pattern?

- **Reliable**: File I/O is more predictable than string manipulation
- **Safe**: Preview changes before applying them
- **Clear**: Each step has a single, well-defined purpose
- **Debuggable**: Intermediate files can be inspected
- **LLM-Friendly**: Matches how AI agents naturally work with code

---

## 🛠️ Use Cases

### For AI Agents

- Automated notebook refactoring
- Batch code updates across multiple notebooks
- Programmatic notebook generation
- CI/CD pipeline integration

### For Developers

- Quick notebook editing without Jupyter
- Scripted notebook modifications
- Version control-friendly notebook updates
- Lightweight notebook manipulation in restricted environments

---

## 📋 Requirements

- **Python 3.6+** (no external packages required)
- Works on Linux, macOS, and Windows

---

## 🔧 Technical Details

### File Format

The tool works with standard Jupyter Notebook format (`.ipynb`), which is JSON-based:

- Preserves all metadata
- Maintains cell execution counts
- Handles both code and markdown cells
- Supports multi-line content with proper formatting

### Safety Features

- Validates JSON structure before saving
- Creates backups implicitly (use version control!)
- Handles edge cases (empty cells, special characters, etc.)
- Provides clear error messages

---

## 📝 Examples

### Example 1: Batch Update Import Statements

```bash
# Find all cells with old import
python notebook_editor.py search notebook.ipynb "from old_module import"

# For each match, update the cell
python notebook_editor.py read notebook.ipynb 3 --to-file temp.py
# Edit temp.py to replace import
python notebook_editor.py update notebook.ipynb 3 --from-file temp.py
```

### Example 2: Add Documentation

```bash
# Add markdown cell at the beginning
python notebook_editor.py add notebook.ipynb --index 0 --type markdown --content "# Analysis Report

This notebook performs data analysis on customer data.

## Author: AI Agent
## Date: 2025-11-27"
```

### Example 3: Clean Up Debug Code

```bash
# Search for debug prints
python notebook_editor.py search notebook.ipynb "print.*debug" --regex

# Delete cells with debug code
python notebook_editor.py delete notebook.ipynb 7
python notebook_editor.py delete notebook.ipynb 12
```

---

## 🤝 Contributing

Contributions are welcome! This tool is designed to be simple and focused. When contributing:

1. Maintain zero-dependency principle
2. Keep the CLI interface clean and predictable
3. Ensure compatibility with AI agent workflows
4. Add tests for new features

---

## 📄 License

MIT License - feel free to use in your projects!

---

## 🙏 Acknowledgments

Built for the AI agent community to enable seamless notebook manipulation in automated workflows.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/notebook-editor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/notebook-editor/discussions)

---

**Made with ❤️ for AI Agents and Developers**
