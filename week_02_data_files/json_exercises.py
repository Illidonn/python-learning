import json
import os.path


def save_json(filename, obj):
    """Сохраняет Python-объект в JSON-файл (перезаписывает, если файл существует)."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(filename):
    """Читает JSON-файл и возвращает Python-объект."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def increment_counter(filename):
    """Увеличивает счётчик запусков в JSON-файле на 1.

    Если файла нет — создаёт его со значением 1.
    Возвращает новое значение счётчика.
    """
    if os.path.exists(filename):
        data = load_json(filename)
    else:
        counter = {"count": 0}
    data["count"] = data.get("count", 0) + 1
    save_json(filename, data)
    return data["count"]
        
count = increment_counter("necron_2.json")
print(f"Запуск номер {count}")
