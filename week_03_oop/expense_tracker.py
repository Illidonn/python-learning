import json
from dataclasses import dataclass, asdict
from datetime import date
FILENAME = "expenses.json"

@dataclass
class Expense:
    """Один расход: сумма, категория, комментарий, дата создания."""

    amount: float
    category: str
    comment: str = ""
    date: str = ""

    def __post_init__(self):
        #комментарий для примера отслеживания изменений в git
        if not self.date:
            self.date = date.today().isoformat()

    def describe(self):
        """Возвращает строку с описанием расхода для печати."""
        if self.comment:
            return f"{self.date} | {self.category} | {self.amount} ₽ ({self.comment})"
        return f"{self.date} | {self.category} | {self.amount} ₽"
    
@dataclass
class RecurringExpense(Expense):
    """Определён для упражнения, в трекер не идёт."""
    period: str = ""

    def describe(self):
       
        result = super().describe()
        return f"{result} | повторяется: {self.period}"

class ExpenseTracker:
    """Управляет списком расходов: добавление, агрегации, вывод."""

    def __init__(self, filename):
        self.filename = filename
        self.load()

    
    def load(self):
        """Читает JSON-файл. Превращает словари из него в пригодные для использования в Expense.
        Если файла нет - self.expenses остаётся пустым списком."""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.expenses = [Expense(
                                amount=d["amount"],
                                category=d["category"],
                                comment=d["comment"],
                                date=d["date"],
                            ) for d in data]
        except FileNotFoundError:
            self.expenses = []


    def add(self, expense):
        """Добавляет расход в трекер."""
        self.expenses.append(expense)
        self.save()

    def save(self):
        """Cохраняет все расходы в JSON-файл."""
        data = [asdict(expense) for expense in self.expenses]

        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


    def total(self):
        """Возвращает общую сумму всех расходов."""
        return sum(expense.amount for expense in self.expenses)

    def total_by_category(self):
        """Возвращает словарь {категория: сумма}."""
        totals = {}
        for expense in self.expenses:
            category = expense.category
            totals[category] = totals.get(category, 0) + expense.amount
        return totals

    def show_all(self):
        """Печатает все расходы в порядке добавления.
        Если список пуст — сообщение об отсутствии данных.
        """
        if not self.expenses:
            print("Расходов пока нет")
            return

        for expense in self.expenses:
            print(expense.describe())

def main():
    """Калькулятор расходов с сохранением данных в json-файл
    Если файла нет, то создаёт его"""
    tracker = ExpenseTracker(FILENAME)

    while True:
        
        print("\n1. Добавить трату")
        print("2. Показать все траты")
        print("3. Итог по категориям")
        print("4. Общая сумма")
        print("5. Выход")

        choice = input("Выбор: ").strip()

        if choice == "1":
            while True:
                try:
                    amount = float(input("Введите сумму: ").strip())
                    break
                except ValueError:
                    print('Ошибка. Пожалуйста введите числовое значение.')

            print("\n1. Еда.")
            print("2. Транспорт.")
            print("3. Развлечения.")
            print("4. Прочее.")
            mapping_category = {"1": "Еда", "2": "Транспорт", "3": "Развлечения", "4": "Прочее"}

            while True:
                try:
                    category = mapping_category[input("Выберите категорию.")]
                    break
                except KeyError:
                    print("Ошибка. Нет такой категории.")

            comment = input("Примечание: (оставьте пустым, если не требуется)").strip()

            tracker.add(Expense(amount=amount, category=category, comment=comment))
            print("Добавлено.")

        elif choice == "2":
            tracker.show_all()
            
        elif choice == "3":
            for c, a in tracker.total_by_category().items():
                print(f"Категория: {c}, Сумма: {a} ₽")
            
        elif choice == "4": 
            print(f"Всего: {tracker.total()} ₽")
            
        elif choice == "5":
            break

        else: 
            print("Нет такого пункта.")

if __name__ == "__main__":
    main()

#тестовый коммент