#!/usr/bin/env python3
"""
Инструмент для редактирования Jupyter Notebook файлов агентами.
Работаем без внешних зависимостей, сохраняем структуру JSON.
"""
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
    """
    Класс для работы с Jupyter Notebook файлами.
    Загружаем, редактируем, сохраняем ноутбуки программно.
    """
    
    def __init__(self, filepath: str):
        """
        Инициализируем редактор ноутбука.
        
        params:
            filepath: Путь к .ipynb файлу
        return:
            None
        """
        self.filepath = Path(filepath)
        self.data = self._load_notebook()

    def _load_notebook(self) -> Dict[str, Any]:
        """
        Загружаем JSON ноутбука. Создаём новый если файл не существует.
        
        params:
            None
        return:
            Dict с данными ноутбука
        """
        if not self.filepath.exists():
            # Создаём минимальную структуру ноутбука
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
        """
        Сохраняем текущее состояние ноутбука в файл.
        
        params:
            None
        return:
            None
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=1, ensure_ascii=False)
            # Добавляем перенос строки в конец файла
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write('\n')
        except Exception as e:
            print(f"Error saving file: {e}")
            sys.exit(1)

    def _normalize_source(self, source: Union[str, List[str]]) -> List[str]:
        """
        Нормализуем source в список строк с переносами.
        
        params:
            source: Строка или список строк
        return:
            Список строк с сохранёнными переносами
        """
        if isinstance(source, str):
            # Разбиваем по строкам, сохраняем переносы
            lines = source.splitlines(keepends=True)
            return lines
        return source

    def _source_to_string(self, source: Union[str, List[str]]) -> str:
        """
        Конвертируем source в единую строку.
        
        params:
            source: Строка или список строк
        return:
            Объединённая строка
        """
        if isinstance(source, list):
            return "".join(source)
        return source

    def _get_cell_outputs(self, outputs: List[Dict[str, Any]]) -> str:
        """
        Парсим выводы ячейки в читаемую строку.
        
        params:
            outputs: Список объектов вывода ячейки
        return:
            Форматированная строка с выводами
        """
        result = []
        for i, output in enumerate(outputs):
            output_type = output.get('output_type', '')
            result.append(f"--- Output {i} ({output_type}) ---")
            
            if output_type == 'stream':
                text = self._source_to_string(output.get('text', []))
                result.append(text.rstrip())
                
            elif output_type in ('execute_result', 'display_data'):
                data = output.get('data', {})
                # Пробуем получить текстовое представление
                if 'text/plain' in data:
                    text = self._source_to_string(data['text/plain'])
                    result.append(text.rstrip())
                
                # Проверяем наличие изображений или бинарных данных
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
            
            result.append("")  # Пустая строка после вывода
            
        return "\n".join(result)

    def list_cells(self, limit: int = 0):
        """
        Выводим список ячеек с превью содержимого.
        
        params:
            limit: Максимальное количество ячеек для вывода (0 = все)
        return:
            None
        """
        cells = self.data.get('cells', [])
        print(f"Total cells: {len(cells)}")
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', 'unknown').upper()
            source = self._normalize_source(cell.get('source', []))
            
            # Превью кода (первые 2 + последние 2 строки)
            source_lines = [line.rstrip() for line in source]
            if not source_lines:
                preview_source = ""
            elif len(source_lines) <= 4:
                preview_source = "\n".join([f"    | {line}" for line in source_lines])
            else:
                first_two = [f"    | {line}" for line in source_lines[:2]]
                last_two = [f"    | {line}" for line in source_lines[-2:]]
                preview_source = "\n".join(first_two + ["    | ..."] + last_two)

            # Превью вывода
            outputs = cell.get('outputs', [])
            output_info = []
            if outputs:
                output_info.append("    [OUTPUTS DETAILS]:")
                
                # Проверяем наличие изображений и текста
                has_image = False
                text_lines_found = []
                
                for output in outputs:
                    # Извлекаем текст
                    text_content = []
                    if output.get('output_type') == 'stream':
                        text_content = self._normalize_source(output.get('text', []))
                    elif 'data' in output and 'text/plain' in output['data']:
                        text_content = self._normalize_source(output['data']['text/plain'])
                    
                    if text_content and len(text_lines_found) < 2:
                        for line in text_content:
                            if line.strip() and len(text_lines_found) < 2:
                                text_lines_found.append(line.rstrip())
                    
                    # Определяем наличие изображений
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
            
            # Выводим информацию о ячейке
            print(f"[{i}] {cell_type}:")
            if preview_source:
                print(preview_source)
            if output_info:
                print("\n".join(output_info))
            print("")  # Разделитель

            if limit > 0 and i >= limit - 1:
                print("... (limit reached)")
                break

    def save_output(self, cell_index: int, output_index: int, to_file: str):
        """
        Сохраняем бинарный вывод (изображение) в файл.
        
        params:
            cell_index: Индекс ячейки
            output_index: Индекс вывода внутри ячейки
            to_file: Путь к файлу для сохранения
        return:
            None
        """
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
        
        # Ищем подходящий бинарный ключ
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
        
        # Объединяем если это список
        if isinstance(b64_data, list):
            b64_data = "".join(b64_data)
        
        # Убираем переносы строк
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
        """
        Добавляем новую ячейку в ноутбук.
        
        params:
            index: Позиция для вставки (-1 = в конец)
            cell_type: Тип ячейки ('code' или 'markdown')
            content: Содержимое ячейки
        return:
            None
        """
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
        """
        Удаляем ячейку из ноутбука.
        
        params:
            index: Индекс удаляемой ячейки
        return:
            None
        """
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range.")
            sys.exit(1)
        
        deleted = cells.pop(index)
        print(f"Deleted cell {index} ({deleted.get('cell_type')}).")
        self.save()

    def update_cell(self, index: int, content: str, clear_outputs: bool = True):
        """
        Обновляем содержимое ячейки.
        
        params:
            index: Индекс ячейки
            content: Новое содержимое
            clear_outputs: Очищаем ли выводы (по умолчанию True)
        return:
            None
        """
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
        """
        Ищем текст в ячейках (в коде и выводах).
        
        params:
            query: Строка поиска или regex-паттерн
            use_regex: Использовать ли regex (по умолчанию False)
        return:
            None
        """
        cells = self.data.get('cells', [])
        results = set()
        
        for i, cell in enumerate(cells):
            # 1. Ищем в исходном коде
            source = self._source_to_string(cell.get('source', []))
            match_found = False
            
            # Вспомогательная функция для проверки совпадения
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

            # 2. Ищем в выводах
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
        """
        Показываем diff между текущим и новым содержимым ячейки.
        
        params:
            index: Индекс ячейки
            new_content: Новое содержимое для сравнения
        return:
            None
        """
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range.")
            sys.exit(1)

        current_source = self._source_to_string(cells[index].get('source', []))
        
        # Подготавливаем для diff
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

    def clear_outputs(self, indices: Optional[List[int]] = None):
        """
        Очищаем выводы ячеек.
        
        params:
            indices: Список индексов для очистки (None = все code-ячейки)
        return:
            None
        """
        cells = self.data.get('cells', [])
        cleared_count = 0
        
        if indices is None:
            # Очищаем все code-ячейки
            for cell in cells:
                if cell.get('cell_type') == 'code':
                    cell['outputs'] = []
                    cell['execution_count'] = None
                    cleared_count += 1
            print(f"Cleared outputs of {cleared_count} code cells.")
        else:
            for i in indices:
                if i < 0 or i >= len(cells):
                    print(f"Warning: Cell index {i} out of range, skipping.")
                    continue
                if cells[i].get('cell_type') != 'code':
                    print(f"Warning: Cell {i} is not a code cell, skipping.")
                    continue
                cells[i]['outputs'] = []
                cells[i]['execution_count'] = None
                cleared_count += 1
                print(f"Cleared output of cell {i}.")
        
        if cleared_count > 0:
            self.save()

    def patch_lines(self, index: int, start_line: int, end_line: int, 
                    new_content: str, preserve_indent: bool = True, insert_mode: bool = False):
        """
        Заменяем строки с start_line по end_line на new_content.
        
        params:
            index: Индекс ячейки
            start_line: Начальная строка (1-indexed)
            end_line: Конечная строка (1-indexed, включительно)
            new_content: Новое содержимое для замены
            preserve_indent: Сохраняем ли отступ первой строки (по умолчанию True)
            insert_mode: Вставляем после start_line вместо замены (по умолчанию False)
        return:
            None
        """
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range (0-{len(cells)-1})")
            sys.exit(1)

        source = self._source_to_string(cells[index].get('source', []))
        lines = source.splitlines(keepends=True)
        
        # Конвертируем в 0-indexed
        start = start_line - 1
        end = end_line  # end_line включительно, но используем как exclusive
        
        # Валидируем диапазон
        if start < 0:
            print(f"Error: start_line must be >= 1")
            sys.exit(1)
        if end > len(lines):
            print(f"Error: end_line ({end_line}) exceeds total lines ({len(lines)})")
            sys.exit(1)
        if start > end and not insert_mode:
            print(f"Error: start_line ({start_line}) > end_line ({end_line})")
            sys.exit(1)
        
        # Обрабатываем режим вставки
        if insert_mode:
            # Вставляем после start_line
            insert_pos = start_line  # Вставляем после этой строки
            if insert_pos > len(lines):
                insert_pos = len(lines)
            
            new_lines = new_content.splitlines(keepends=True)
            # Гарантируем перенос в конце
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            
            if preserve_indent and insert_pos > 0 and lines[insert_pos - 1] and new_lines:
                # Вычисляем дельту отступов
                ref_line = lines[insert_pos - 1]
                original_indent = len(ref_line) - len(ref_line.lstrip())
                
                # Находим базовый отступ нового контента
                new_first_line = next((l for l in new_lines if l.strip()), new_lines[0])
                new_indent = len(new_first_line) - len(new_first_line.lstrip())
                
                indent_delta = original_indent - new_indent
                
                # Применяем дельту ко всем строкам
                adjusted_lines = []
                for line in new_lines:
                    if line.strip():  # Непустая строка
                        if indent_delta > 0:
                            adjusted_lines.append(' ' * indent_delta + line)
                        elif indent_delta < 0:
                            current_indent = len(line) - len(line.lstrip())
                            remove = min(-indent_delta, current_indent)
                            adjusted_lines.append(line[remove:])
                        else:
                            adjusted_lines.append(line)
                    else:
                        adjusted_lines.append(line)
                new_lines = adjusted_lines
            
            new_source = ''.join(lines[:insert_pos]) + ''.join(new_lines) + ''.join(lines[insert_pos:])
            cells[index]['source'] = self._normalize_source(new_source)
            print(f"Inserted {len(new_lines)} lines after line {start_line} in cell {index}.")
        else:
            # Режим замены
            new_lines = new_content.splitlines(keepends=True)
            # Гарантируем перенос если заменяем в середине
            if new_lines and end < len(lines) and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            
            if preserve_indent and start < len(lines) and lines[start] and new_lines:
                # Вычисляем дельту отступов
                original_indent = len(lines[start]) - len(lines[start].lstrip())
                # Находим базовый отступ нового контента
                new_first_line = next((l for l in new_lines if l.strip()), new_lines[0])
                new_indent = len(new_first_line) - len(new_first_line.lstrip())
                
                indent_delta = original_indent - new_indent
                
                # Применяем дельту ко всем строкам
                adjusted_lines = []
                for line in new_lines:
                    if line.strip():  # Непустая строка
                        if indent_delta > 0:
                            # Добавляем пробелы
                            adjusted_lines.append(' ' * indent_delta + line)
                        elif indent_delta < 0:
                            # Убираем пробелы (но не больше чем есть)
                            current_indent = len(line) - len(line.lstrip())
                            remove = min(-indent_delta, current_indent)
                            adjusted_lines.append(line[remove:])
                        else:
                            adjusted_lines.append(line)
                    else:
                        adjusted_lines.append(line)
                new_lines = adjusted_lines
            
            new_source = ''.join(lines[:start]) + ''.join(new_lines) + ''.join(lines[end:])
            cells[index]['source'] = self._normalize_source(new_source)
            print(f"Replaced lines {start_line}-{end_line} in cell {index}.")
        
        # Очищаем выводы так как код изменился
        if cells[index].get('cell_type') == 'code':
            cells[index]['outputs'] = []
            cells[index]['execution_count'] = None
        
        self.save()

    def read_cell(self, index: int, to_file: Optional[str] = None, 
                  include_output: bool = False, numbered: bool = False):
        """
        Читаем содержимое ячейки с опциональной нумерацией строк.
        
        params:
            index: Индекс ячейки
            to_file: Путь для сохранения в файл (опционально)
            include_output: Включаем ли вывод ячейки (по умолчанию False)
            numbered: Показываем ли номера строк (по умолчанию False)
        return:
            None
        """
        cells = self.data.get('cells', [])
        if index < 0 or index >= len(cells):
            print(f"Error: Cell index {index} out of range (0-{len(cells)-1})")
            sys.exit(1)

        cell = cells[index]
        source_content = self._source_to_string(cell.get('source', []))
        
        # Добавляем номера строк если запрошено
        if numbered:
            source_lines = source_content.splitlines(keepends=True)
            # Вычисляем ширину для номеров строк
            width = len(str(len(source_lines)))
            numbered_lines = [f"{i+1:>{width}}: {line}" for i, line in enumerate(source_lines)]
            source_content = ''.join(numbered_lines)
        
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
            print(f"--- Cell {index} ({cell.get('cell_type')}) [{len(source_content.splitlines())} lines] ---")
            print(full_content)
            print("---------------------------")

    def info(self):
        """
        Показываем метаданные и статистику ноутбука.
        
        params:
            None
        return:
            None
        """
        cells = self.data.get('cells', [])
        
        code_cells = sum(1 for c in cells if c.get('cell_type') == 'code')
        markdown_cells = sum(1 for c in cells if c.get('cell_type') == 'markdown')
        cells_with_output = sum(1 for c in cells if c.get('outputs'))
        
        total_lines = 0
        for cell in cells:
            source = self._source_to_string(cell.get('source', []))
            total_lines += len(source.splitlines())
        
        # Получаем информацию о ядре
        kernel = self.data.get('metadata', {}).get('kernelspec', {}).get('display_name', 'Unknown')
        nbformat = self.data.get('nbformat', '?')
        nbformat_minor = self.data.get('nbformat_minor', '?')
        
        print(f"Notebook: {self.filepath}")
        print(f"Format: nbformat {nbformat}.{nbformat_minor}")
        print(f"Kernel: {kernel}")
        print(f"Cells: {len(cells)} total")
        print(f"  - Code: {code_cells}")
        print(f"  - Markdown: {markdown_cells}")
        print(f"  - With outputs: {cells_with_output}")
        print(f"Total source lines: {total_lines}")

    def validate(self) -> bool:
        """
        Проверяем валидность структуры ноутбука.
        
        params:
            None
        return:
            True если ноутбук валиден, иначе False
        """
        errors = []
        warnings = []
        
        # Проверяем обязательные поля верхнего уровня
        if 'cells' not in self.data:
            errors.append("Missing required field 'cells'")
        if 'nbformat' not in self.data:
            errors.append("Missing required field 'nbformat'")
        if 'metadata' not in self.data:
            warnings.append("Missing 'metadata' field")
        
        # Проверяем каждую ячейку
        cells = self.data.get('cells', [])
        for i, cell in enumerate(cells):
            if 'cell_type' not in cell:
                errors.append(f"Cell {i}: Missing 'cell_type'")
            elif cell['cell_type'] not in ('code', 'markdown', 'raw'):
                warnings.append(f"Cell {i}: Unknown cell_type '{cell['cell_type']}'")
            
            if 'source' not in cell:
                errors.append(f"Cell {i}: Missing 'source'")
            
            if cell.get('cell_type') == 'code':
                if 'outputs' not in cell:
                    warnings.append(f"Cell {i}: Code cell missing 'outputs'")
        
        # Выводим результаты
        if errors:
            print("ERRORS:")
            for e in errors:
                print(f"  ✗ {e}")
        
        if warnings:
            print("WARNINGS:")
            for w in warnings:
                print(f"  ⚠ {w}")
        
        if not errors and not warnings:
            print("✓ Notebook is valid")
        elif not errors:
            print(f"✓ Notebook is valid ({len(warnings)} warnings)")
        else:
            print(f"✗ Notebook has {len(errors)} errors")
        
        return len(errors) == 0

    def list_cells_json(self, limit: int = 0) -> str:
        """
        Возвращаем список ячеек в формате JSON для парсинга LLM.
        
        params:
            limit: Максимальное количество ячеек (0 = все)
        return:
            JSON-строка с информацией о ячейках
        """
        cells = self.data.get('cells', [])
        result = {
            "notebook": str(self.filepath),
            "total_cells": len(cells),
            "cells": []
        }
        
        for i, cell in enumerate(cells):
            if limit > 0 and i >= limit:
                break
            
            source = self._source_to_string(cell.get('source', []))
            source_lines = source.splitlines()
            
            cell_info = {
                "index": i,
                "type": cell.get('cell_type', 'unknown'),
                "lines": len(source_lines),
                "has_output": bool(cell.get('outputs', [])),
                "preview_first": source_lines[0][:80] if source_lines else "",
                "preview_last": source_lines[-1][:80] if source_lines else ""
            }
            
            # Проверяем наличие изображений в выводах
            for output in cell.get('outputs', []):
                if 'data' in output:
                    for key in output['data']:
                        if key.startswith('image/'):
                            cell_info["has_image"] = True
                            break
            
            result["cells"].append(cell_info)
        
        return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    """
    Главная функция CLI. Парсим аргументы и вызываем соответствующие методы.
    """
    parser = argparse.ArgumentParser(description="Agent-Native Jupyter Notebook Editor")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Общий аргумент для пути к ноутбуку
    def add_nb_arg(p):
        p.add_argument("notebook", help="Path to the .ipynb file")

    # LIST
    parser_list = subparsers.add_parser("list", help="List cells in the notebook")
    add_nb_arg(parser_list)
    parser_list.add_argument("--limit", type=int, default=0, help="Limit output lines")
    parser_list.add_argument("--json", action="store_true", help="Output as JSON (for LLM parsing)")

    # READ
    parser_read = subparsers.add_parser("read", help="Read a cell")
    add_nb_arg(parser_read)
    parser_read.add_argument("index", type=int, help="Cell index")
    parser_read.add_argument("--to-file", help="Save content to this file")
    parser_read.add_argument("--include-output", action="store_true", help="Include cell output in the result")
    parser_read.add_argument("--numbered", action="store_true", help="Show line numbers")

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

    # CLEAR-OUTPUT
    parser_clear = subparsers.add_parser("clear-output", help="Clear cell outputs")
    add_nb_arg(parser_clear)
    clear_group = parser_clear.add_mutually_exclusive_group(required=True)
    clear_group.add_argument("--all", action="store_true", help="Clear outputs of all code cells")
    clear_group.add_argument("--cells", type=int, nargs="+", help="Cell indices to clear")

    # PATCH
    parser_patch = subparsers.add_parser("patch", help="Edit specific lines in a cell")
    add_nb_arg(parser_patch)
    parser_patch.add_argument("index", type=int, help="Cell index")
    parser_patch.add_argument("--lines", required=True, help="Line range to replace (e.g. 5-10)")
    patch_group = parser_patch.add_mutually_exclusive_group(required=True)
    patch_group.add_argument("--content", help="New content string")
    patch_group.add_argument("--from-file", help="Read new content from this file")
    parser_patch.add_argument("--insert", action="store_true", help="Insert after start line instead of replacing")
    parser_patch.add_argument("--no-preserve-indent", action="store_true", help="Don't preserve original indentation")

    # INFO
    parser_info = subparsers.add_parser("info", help="Show notebook metadata and statistics")
    add_nb_arg(parser_info)

    # VALIDATE
    parser_validate = subparsers.add_parser("validate", help="Validate notebook structure")
    add_nb_arg(parser_validate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    editor = NotebookEditor(args.notebook)

    # Вспомогательная функция для получения контента
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
        if args.json:
            print(editor.list_cells_json(args.limit))
        else:
            editor.list_cells(args.limit)
    
    elif args.command == "read":
        editor.read_cell(args.index, args.to_file, args.include_output, args.numbered)
    
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
        editor.save()  # __init__ создаёт структуру, save записывает
        print(f"Created new notebook at {args.notebook}")

    elif args.command == "save-output":
        editor.save_output(args.index, args.output_index, args.to_file)

    elif args.command == "clear-output":
        if args.all:
            editor.clear_outputs(None)
        else:
            editor.clear_outputs(args.cells)

    elif args.command == "patch":
        content = get_content(args)
        # Парсим диапазон строк
        try:
            parts = args.lines.split('-')
            start_line = int(parts[0])
            end_line = int(parts[1]) if len(parts) > 1 else start_line
        except ValueError:
            print(f"Error: Invalid line range format '{args.lines}'. Use format: 5-10 or 5")
            sys.exit(1)
        editor.patch_lines(
            args.index, start_line, end_line, content,
            preserve_indent=not args.no_preserve_indent,
            insert_mode=args.insert
        )

    elif args.command == "info":
        editor.info()

    elif args.command == "validate":
        if not editor.validate():
            sys.exit(1)


if __name__ == "__main__":
    main()
