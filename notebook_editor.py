#!/usr/bin/env python3
import json
import argparse
import sys
import os
import difflib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class NotebookEditor:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = self._load_notebook()

    def _load_notebook(self) -> Dict[str, Any]:
        """Loads the notebook JSON. Creates a new one if it doesn't exist."""
        if not self.filepath.exists():
            # Create a new minimal notebook structure
            return {
                "cells": [],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "codemirror_mode": {"name": "ipython", "version": 3},
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3.8.0"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5
            }
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: File '{self.filepath}' is not a valid JSON file.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)

    def save(self):
        """Saves the current state of the notebook to the file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=1, ensure_ascii=False)
            # Add a newline at the end of the file for good measure
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write('\n')
        except Exception as e:
            print(f"Error saving file: {e}")
            sys.exit(1)

    def _normalize_source(self, source: Union[str, List[str]]) -> List[str]:
        """Ensures source is always a list of strings with proper newlines."""
        if isinstance(source, str):
            # Split by lines and keep newlines
            lines = source.splitlines(keepends=True)
            # If the last line doesn't have a newline, splitlines might not add it if it wasn't there.
            # But standard behavior for list of strings in ipynb is usually to have \n at end of each line except maybe last.
            # Let's just ensure it's a list.
            return lines
        return source

    def _source_to_string(self, source: Union[str, List[str]]) -> str:
        """Converts source list/string to a single string."""
        if isinstance(source, list):
            return "".join(source)
        return source

    def list_cells(self, limit: int = 0):
        """Lists cells with summary."""
        cells = self.data.get('cells', [])
        print(f"Total cells: {len(cells)}")
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', 'unknown').upper()
            source = self._normalize_source(cell.get('source', []))
            
            preview = ""
            if source:
                first_line = source[0].strip()
                preview = first_line[:60] + "..." if len(first_line) > 60 else first_line
            
            print(f"[{i}] {cell_type}: {preview}")
            if limit > 0 and i >= limit - 1:
                print("... (limit reached)")
                break

    def read_cell(self, index: int, to_file: Optional[str] = None):
        """Reads a specific cell."""
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range (0-{len(cells)-1})")
            sys.exit(1)

        cell = cells[index]
        source_content = self._source_to_string(cell.get('source', []))

        if to_file:
            try:
                with open(to_file, 'w', encoding='utf-8') as f:
                    f.write(source_content)
                print(f"Cell {index} content written to '{to_file}'")
            except Exception as e:
                print(f"Error writing to file: {e}")
                sys.exit(1)
        else:
            print(f"--- Cell {index} ({cell.get('cell_type')}) ---")
            print(source_content)
            print("---------------------------")

    def add_cell(self, index: int, cell_type: str, content: str):
        """Adds a new cell."""
        new_cell = {
            "cell_type": cell_type,
            "metadata": {},
            "source": self._normalize_source(content)
        }
        if cell_type == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []

        cells = self.data.get('cells', [])
        
        if index == -1:
            cells.append(new_cell)
            print(f"Added new {cell_type} cell at the end (index {len(cells)-1}).")
        else:
            if index < 0: index = 0
            if index > len(cells): index = len(cells)
            cells.insert(index, new_cell)
            print(f"Inserted new {cell_type} cell at index {index}.")
        
        self.save()

    def delete_cell(self, index: int):
        """Deletes a cell."""
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range.")
            sys.exit(1)
        
        deleted = cells.pop(index)
        print(f"Deleted cell {index} ({deleted.get('cell_type')}).")
        self.save()

    def update_cell(self, index: int, content: str, clear_outputs: bool = True):
        """Updates content of a cell."""
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range.")
            sys.exit(1)

        cell = cells[index]
        cell['source'] = self._normalize_source(content)
        
        if cell['cell_type'] == 'code' and clear_outputs:
            cell['execution_count'] = None
            cell['outputs'] = []
            
        print(f"Updated cell {index}.")
        self.save()

    def search(self, query: str, use_regex: bool = False):
        """Searches for text in cells."""
        cells = self.data.get('cells', [])
        results = []
        
        for i, cell in enumerate(cells):
            source = self._source_to_string(cell.get('source', []))
            match = False
            if use_regex:
                if re.search(query, source, re.MULTILINE):
                    match = True
            else:
                if query in source:
                    match = True
            
            if match:
                results.append(i)
                print(f"Match in Cell [{i}] ({cell.get('cell_type')}):")
                # Show context (line with match)
                lines = source.splitlines()
                for line in lines:
                    if (use_regex and re.search(query, line)) or (not use_regex and query in line):
                        print(f"  > {line.strip()[:80]}")

        if not results:
            print("No matches found.")
        else:
            print(f"Found matches in {len(results)} cells: {results}")

    def show_diff(self, index: int, new_content: str):
        """Shows diff between current cell content and new content."""
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range.")
            sys.exit(1)

        current_source = self._source_to_string(cells[index].get('source', []))
        
        # Prepare for diff
        current_lines = current_source.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            current_lines, 
            new_lines, 
            fromfile=f'Cell {index} (Current)', 
            tofile='New Content',
            lineterm=''
        )
        
        diff_text = "".join(diff)
        if diff_text:
            print(diff_text)
        else:
            print("No differences found.")

def main():
    parser = argparse.ArgumentParser(description="Agent-Native Jupyter Notebook Editor")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Common argument for notebook path
    def add_nb_arg(p):
        p.add_argument("notebook", help="Path to the .ipynb file")

    # LIST
    parser_list = subparsers.add_parser("list", help="List cells in the notebook")
    add_nb_arg(parser_list)
    parser_list.add_argument("--limit", type=int, default=0, help="Limit output lines")

    # READ
    parser_read = subparsers.add_parser("read", help="Read a cell")
    add_nb_arg(parser_read)
    parser_read.add_argument("index", type=int, help="Cell index")
    parser_read.add_argument("--to-file", help="Save content to this file")

    # SEARCH
    parser_search = subparsers.add_parser("search", help="Search in notebook")
    add_nb_arg(parser_search)
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument("--regex", action="store_true", help="Use regex search")

    # UPDATE
    parser_update = subparsers.add_parser("update", help="Update a cell")
    add_nb_arg(parser_update)
    parser_update.add_argument("index", type=int, help="Cell index")
    group = parser_update.add_mutually_exclusive_group(required=True)
    group.add_argument("--content", help="New content string")
    group.add_argument("--from-file", help="Read new content from this file")
    parser_update.add_argument("--no-clear-output", action="store_true", help="Don't clear cell outputs")

    # ADD
    parser_add = subparsers.add_parser("add", help="Add a new cell")
    add_nb_arg(parser_add)
    parser_add.add_argument("--index", type=int, default=-1, help="Insertion index (-1 for end)")
    parser_add.add_argument("--type", choices=["code", "markdown"], default="code", help="Cell type")
    group_add = parser_add.add_mutually_exclusive_group(required=True)
    group_add.add_argument("--content", help="Content string")
    group_add.add_argument("--from-file", help="Read content from this file")

    # DELETE
    parser_delete = subparsers.add_parser("delete", help="Delete a cell")
    add_nb_arg(parser_delete)
    parser_delete.add_argument("index", type=int, help="Cell index")

    # DIFF
    parser_diff = subparsers.add_parser("diff", help="Show diff for a cell update")
    add_nb_arg(parser_diff)
    parser_diff.add_argument("index", type=int, help="Cell index")
    group_diff = parser_diff.add_mutually_exclusive_group(required=True)
    group_diff.add_argument("--content", help="New content string")
    group_diff.add_argument("--from-file", help="Read new content from this file")

    # CREATE
    parser_create = subparsers.add_parser("create", help="Create a new empty notebook")
    add_nb_arg(parser_create)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    editor = NotebookEditor(args.notebook)

    # Helper to get content
    def get_content(args_obj):
        if hasattr(args_obj, 'from_file') and args_obj.from_file:
            try:
                with open(args_obj.from_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading input file: {e}")
                sys.exit(1)
        elif hasattr(args_obj, 'content') and args_obj.content:
            return args_obj.content
        return ""

    if args.command == "list":
        editor.list_cells(args.limit)
    
    elif args.command == "read":
        editor.read_cell(args.index, args.to_file)
    
    elif args.command == "search":
        editor.search(args.query, args.regex)
    
    elif args.command == "update":
        content = get_content(args)
        editor.update_cell(args.index, content, not args.no_clear_output)
    
    elif args.command == "add":
        content = get_content(args)
        editor.add_cell(args.index, args.type, content)
    
    elif args.command == "delete":
        editor.delete_cell(args.index)
        
    elif args.command == "diff":
        content = get_content(args)
        editor.show_diff(args.index, content)
        
    elif args.command == "create":
        editor.save() # __init__ creates the structure, save writes it
        print(f"Created new notebook at {args.notebook}")

if __name__ == "__main__":
    main()
