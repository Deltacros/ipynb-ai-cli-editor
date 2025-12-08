#!/usr/bin/env python3
import json
import argparse
import sys
import os
import difflib
import re
import base64
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
            return lines
        return source

    def _source_to_string(self, source: Union[str, List[str]]) -> str:
        """Converts source list/string to a single string."""
        if isinstance(source, list):
            return "".join(source)
        return source

    def _get_cell_outputs(self, outputs: List[Dict[str, Any]]) -> str:
        """Parses cell outputs into a human-readable string representation."""
        result = []
        for i, output in enumerate(outputs):
            output_type = output.get('output_type', '')
            result.append(f"--- Output {i} ({output_type}) ---")
            
            if output_type == 'stream':
                text = self._source_to_string(output.get('text', []))
                result.append(text.rstrip())
                
            elif output_type in ('execute_result', 'display_data'):
                data = output.get('data', {})
                # Try to get text representation
                if 'text/plain' in data:
                    text = self._source_to_string(data['text/plain'])
                    result.append(text.rstrip())
                
                # Check for images or other binary data
                binary_keys = [k for k in data.keys() if k.startswith('image/') or k == 'application/pdf']
                if binary_keys:
                    for key in binary_keys:
                        result.append(f"[BINARY DATA DETECTED: {key}]")
                        result.append(f"(Use 'save-output' command to extract this data)")
                
                if not 'text/plain' in data and not binary_keys:
                     result.append(f"[Complex Data: {list(data.keys())}]")

            elif output_type == 'error':
                ename = output.get('ename', 'Error')
                evalue = output.get('evalue', '')
                traceback = output.get('traceback', [])
                result.append(f"{ename}: {evalue}")
                if traceback:
                    result.append("\n".join(traceback))
            
            result.append("") # Empty line after output
            
        return "\n".join(result)

    def list_cells(self, limit: int = 0):
        """Lists cells with summary."""
        cells = self.data.get('cells', [])
        print(f"Total cells: {len(cells)}")
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', 'unknown').upper()
            source = self._normalize_source(cell.get('source', []))
            
            # Source Preview (First 2 + Last 2 lines)
            source_lines = [line.rstrip() for line in source]
            if not source_lines:
                preview_source = ""
            elif len(source_lines) <= 4:
                preview_source = "\n".join([f"    | {line}" for line in source_lines])
            else:
                first_two = [f"    | {line}" for line in source_lines[:2]]
                last_two = [f"    | {line}" for line in source_lines[-2:]]
                preview_source = "\n".join(first_two + ["    | ..."] + last_two)

            # Output Preview
            outputs = cell.get('outputs', [])
            output_info = []
            if outputs:
                output_info.append("    [OUTPUTS DETAILS]:")
                
                # Check for images and text
                has_image = False
                text_lines_found = []
                
                for output in outputs:
                    # Text extraction
                    text_content = []
                    if output.get('output_type') == 'stream':
                        text_content = self._normalize_source(output.get('text', []))
                    elif 'data' in output and 'text/plain' in output['data']:
                        text_content = self._normalize_source(output['data']['text/plain'])
                    
                    if text_content and len(text_lines_found) < 2:
                        for line in text_content:
                            if line.strip() and len(text_lines_found) < 2:
                                text_lines_found.append(line.rstrip())
                    
                    # Image detection
                    if 'data' in output:
                        for key in output['data']:
                            if key.startswith('image/'):
                                has_image = True
                                break
                                
                if text_lines_found:
                    for line in text_lines_found:
                        output_info.append(f"    > {line[:80]}")
                    if len(text_lines_found) >= 2:
                         output_info.append("    > ...")

                if has_image:
                     output_info.append("    > [IMAGE DETECTED]")
                
                if not text_lines_found and not has_image:
                    output_info.append("    > [Data present]")
            
            # Print Cell Record
            print(f"[{i}] {cell_type}:")
            if preview_source:
                print(preview_source)
            if output_info:
                print("\n".join(output_info))
            print("") # Separator

            if limit > 0 and i >= limit - 1:
                print("... (limit reached)")
                break

    def read_cell(self, index: int, to_file: Optional[str] = None, include_output: bool = False):
        """Reads a specific cell."""
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range (0-{len(cells)-1})")
            sys.exit(1)

        cell = cells[index]
        source_content = self._source_to_string(cell.get('source', []))
        
        output_content = ""
        if include_output and 'outputs' in cell:
            output_content = "\n\n" + self._get_cell_outputs(cell['outputs'])

        full_content = source_content + output_content

        if to_file:
            try:
                with open(to_file, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                print(f"Cell {index} content written to '{to_file}'")
            except Exception as e:
                print(f"Error writing to file: {e}")
                sys.exit(1)
        else:
            print(f"--- Cell {index} ({cell.get('cell_type')}) ---")
            print(full_content)
            print("---------------------------")

    def save_output(self, cell_index: int, output_index: int, to_file: str):
        """Saves a binary output (e.g. image) to a file."""
        cells = self.data.get('cells', [])
        if cell_index < 0 or cell_index >= len(cells):
            print(f"Error: Cell index {cell_index} out of range.")
            sys.exit(1)
            
        cell = cells[cell_index]
        outputs = cell.get('outputs', [])
        
        if output_index < 0 or output_index >= len(outputs):
            print(f"Error: Output index {output_index} out of range (Cell {cell_index} has {len(outputs)} outputs).")
            sys.exit(1)
            
        output = outputs[output_index]
        data = output.get('data', {})
        
        # Find the best binary candidate if multiple exist, or check specific mime types?
        # For now, we take the first image-like or application/pdf key.
        target_key = None
        for key in data.keys():
            if key.startswith('image/') or key == 'application/pdf':
                target_key = key
                break
        
        if not target_key:
            print(f"Error: No supported binary data found in Output {output_index} of Cell {cell_index}.")
            print(f"Available keys: {list(data.keys())}")
            sys.exit(1)
            
        b64_data = data[target_key]
        
        # If it's a list (some older formats?), join it. Usually base64 in json is a string or list of strings.
        if isinstance(b64_data, list):
            b64_data = "".join(b64_data)
        
        # Remove newlines just in case
        b64_data = b64_data.replace('\n', '')
        
        try:
            decoded_data = base64.b64decode(b64_data)
            with open(to_file, 'wb') as f:
                f.write(decoded_data)
            print(f"Saved {target_key} data from Cell {cell_index}, Output {output_index} to '{to_file}'.")
        except Exception as e:
            print(f"Error saving output to file: {e}")
            sys.exit(1)

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
        """Searches for text in cells (source and outputs)."""
        cells = self.data.get('cells', [])
        results = set()
        
        for i, cell in enumerate(cells):
            # 1. Search in Source
            source = self._source_to_string(cell.get('source', []))
            match_found = False
            
            # Helper for matching
            def check_match(text):
                if use_regex:
                    return bool(re.search(query, text, re.MULTILINE))
                return query in text

            if check_match(source):
                match_found = True
                print(f"Match in Cell [{i}] SOURCE ({cell.get('cell_type')}):")
                lines = source.splitlines()
                for line in lines:
                    if (use_regex and re.search(query, line)) or (not use_regex and query in line):
                        print(f"  > {line.strip()[:80]}")

            # 2. Search in Outputs (if applicable)
            outputs = cell.get('outputs', [])
            for out_idx, output in enumerate(outputs):
                output_text = ""
                if output.get('output_type') == 'stream':
                     output_text = self._source_to_string(output.get('text', []))
                elif 'data' in output and 'text/plain' in output['data']:
                     output_text = self._source_to_string(output['data']['text/plain'])
                elif output.get('output_type') == 'error':
                    output_text = f"{output.get('ename', '')}: {output.get('evalue', '')}"

                if output_text and check_match(output_text):
                    match_found = True
                    print(f"Match in Cell [{i}] OUTPUT {out_idx}:")
                    lines = output_text.splitlines()
                    for line in lines:
                         if (use_regex and re.search(query, line)) or (not use_regex and query in line):
                             print(f"  >> {line.strip()[:80]}")

            if match_found:
                results.add(i)

        if not results:
            print("No matches found.")
        else:
            print(f"Found matches in {len(results)} cells: {sorted(list(results))}")

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
    parser_read.add_argument("--include-output", action="store_true", help="Include cell output in the result")

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

    # SAVE OUTPUT
    parser_save_output = subparsers.add_parser("save-output", help="Save binary output (image) to file")
    add_nb_arg(parser_save_output)
    parser_save_output.add_argument("index", type=int, help="Cell index")
    parser_save_output.add_argument("--output-index", type=int, default=0, help="Index of the output in the cell (default 0)")
    parser_save_output.add_argument("--to-file", required=True, help="Destination file for the output")

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
        editor.read_cell(args.index, args.to_file, args.include_output)
    
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

    elif args.command == "save-output":
        editor.save_output(args.index, args.output_index, args.to_file)

if __name__ == "__main__":
    main()
