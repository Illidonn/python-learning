from datetime import date


class Expense:
    """Один расход: сумма, категория, комментарий, дата создания."""

    def __init__(self, amount, category, comment=""):
        self.amount = amount
        self.category = category
        self.comment = comment
        self.date = date.today().isoformat()

    def describe(self):
        """Возвращает строку с описанием расхода для печати."""
        if self.comment:
            return f"{self.date} | {self.category} | {self.amount} ₽ ({self.comment})"
        return f"{self.date} | {self.category} | {self.amount} ₽"


lunch = Expense(350.25, "Еда", "обед")
metro = Expense(60, "Транспорт")

print(lunch.describe())
print(metro.describe())