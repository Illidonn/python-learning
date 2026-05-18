import json
from datetime import date
FILENAME = "expenses.json"

def save_json(filename, obj):
    """Сохраняет Python-объект в JSON-файл (перезаписывает, если файл существует)."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(filename):
    """Читает JSON-файл и возвращает Python-объект."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def input_expense(expenses):
    """внос данных о тратах"""
    expense = float(input("Введите сумму: "))
    print("\n1. Еда.")
    print("2. Транспорт.")
    print("3. Развлечения.")
    print("4. Прочее.")
    mapping_category = {"1": "Еда", "2": "Транспорт", "3": "Развлечения", "4": "Прочее"}
    category = mapping_category.get(input("\nВведите категорию:"), mapping_category["4"])
    comment = input("Примечание: (если требуется)")
    today = date.today().isoformat()
    expenses.append({"date": today, "amount": expense, "category": category, "comment": comment})

def show_all(expenses):
    """показать все траты"""
    if expenses:
        for expense in expenses:
            print(expense, "\n")
    else:
        print("Данных пока нет")
        
def category_show(expenses):
    """показать суммы по категориям"""
    totals = {}
    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, 0) + expense["amount"]
    return totals
    
def total(expenses):
    """показать сумму всех трат"""
    return sum(expense["amount"] for expense in expenses)

def main():
    """Калькулятор расходов с сохранением данных в json-файл
    Если файла нет, то создаёт его"""
    try:
        expenses = load_json(FILENAME)
    except FileNotFoundError:
        expenses = []


    
    while True:
        
        print("\n1. Добавить трату")
        print("2. Показать все траты")
        print("3. Итог по категориям")
        print("4. Общая сумма")
        print("5. Выход")

        choice = input("Выбор: ")

        if choice == "1":
            input_expense(expenses)
            save_json(FILENAME, expenses)

        elif choice == "2":
            show_all(expenses)
            
            
        elif choice == "3":
            print(category_show(expenses))
            
        elif choice == "4": 
            print(total(expenses))
            
        elif choice == "5":
        
            break

if __name__ == "__main__":
    main()