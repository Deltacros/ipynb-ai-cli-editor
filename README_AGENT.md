# Руководство для AI-Агента: Как использовать notebook_editor.py

Этот инструмент предназначен для безопасного и надежного редактирования файлов Jupyter Notebook (.ipynb).
Он работает без внешних зависимостей и гарантирует сохранение структуры JSON.

## Основной паттерн работы (Best Practice)

Для внесения изменений в код всегда следуй этому алгоритму:

1. **Исследование**: Получи список ячеек, чтобы понять структуру.
    `python notebook_editor.py list <notebook.ipynb>`

2. **Чтение**: Выгрузи содержимое нужной ячейки во временный файл.
    `python notebook_editor.py read <notebook.ipynb> <cell_index> --to-file <temp_file.py>`

3. **Редактирование**: Прочитай `<temp_file.py>`, внеси изменения и сохрани их.

4. **Проверка (Diff)**: (Опционально) Посмотри, что изменится.
    `python notebook_editor.py diff <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

5. **Применение**: Обнови ячейку из файла.
    `python notebook_editor.py update <notebook.ipynb> <cell_index> --from-file <temp_file.py>`

## Справочник команд

### 1. Просмотр структуры (`list`)

Показывает индексы, типы ячеек и начало их содержимого.

```bash
python notebook_editor.py list my_notebook.ipynb --limit 50
```

### 2. Чтение ячейки (`read`)

* **В консоль** (для коротких ячеек):

    ```bash
    python notebook_editor.py read my_notebook.ipynb 5
    ```

* **В файл** (РЕКОМЕНДУЕТСЯ для кода):

    ```bash
    python notebook_editor.py read my_notebook.ipynb 5 --to-file cell_5.py
    ```

### 3. Поиск (`search`)

Находит ячейки, содержащие текст или regex.

```bash
python notebook_editor.py search my_notebook.ipynb "import pandas"
python notebook_editor.py search my_notebook.ipynb "def .*_handler" --regex
```

### 4. Обновление ячейки (`update`)

Заменяет содержимое ячейки. Автоматически очищает output ячейки.

* **Из файла** (Безопасно):

    ```bash
    python notebook_editor.py update my_notebook.ipynb 5 --from-file updated_code.py
    ```

* **Текстом** (Только для одной строки):

    ```bash
    python notebook_editor.py update my_notebook.ipynb 5 --content "print('done')"
    ```

### 5. Добавление ячейки (`add`)

Вставляет новую ячейку перед указанным индексом (или в конец, если index=-1).

```bash
python notebook_editor.py add my_notebook.ipynb --index 0 --type markdown --content "# Заголовок"
python notebook_editor.py add my_notebook.ipynb --type code --from-file new_script.py
```

### 6. Удаление ячейки (`delete`)

```bash
python notebook_editor.py delete my_notebook.ipynb 5
```

### 7. Создание ноутбука (`create`)

Создает пустой валидный .ipynb файл.

```bash
python notebook_editor.py create new_notebook.ipynb
```
