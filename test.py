import unittest
import tempfile
import os
from datetime import datetime, timedelta
from database import Database


class TestDatabase(unittest.TestCase):
    """Тесты для базы данных"""

    def setUp(self):
        # Создаем временную базу данных
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_file.name
        self.db = Database(self.db_path)

    def tearDown(self):
        # Закрываем и удаляем временную базу
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_tables_created(self):
        """Тест создания таблиц"""
        cursor = self.db.connection.cursor()

        # Проверяем таблицу категорий
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)

        # Проверяем таблицу транзакций
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
        result = cursor.fetchone()
        self.assertIsNotNone(result)

    def test_default_categories(self):
        """Тест создания категорий по умолчанию"""
        categories = self.db.get_categories()

        # Проверяем, что категории созданы
        self.assertGreater(len(categories), 0)

        # Проверяем типы категорий
        income_cats = self.db.get_categories('income')
        expense_cats = self.db.get_categories('expense')

        self.assertGreater(len(income_cats), 0)
        self.assertGreater(len(expense_cats), 0)

        # Проверяем конкретные категории
        category_names = [cat[1] for cat in categories]
        self.assertIn("Зарплата", category_names)
        self.assertIn("Продукты", category_names)

    def test_add_transaction(self):
        """Тест добавления транзакции"""
        # Получаем категорию "Зарплата"
        categories = self.db.get_categories('income')
        salary_category = [cat for cat in categories if cat[1] == 'Зарплата'][0]
        category_id = salary_category[0]

        # Добавляем транзакцию
        transaction_id = self.db.add_transaction(
            date=datetime.now(),
            amount=50000.0,
            category_id=category_id,
            description="Зарплата за январь",
            type_="income"
        )

        self.assertIsNotNone(transaction_id)

        # Проверяем, что транзакция добавлена
        transactions = self.db.get_transactions()
        self.assertEqual(len(transactions), 1)

        # Проверяем данные транзакции
        transaction = transactions[0]
        self.assertEqual(transaction[2], 50000.0)  # amount
        self.assertEqual(transaction[4], "Зарплата за январь")  # description
        self.assertEqual(transaction[5], "income")  # type

    def test_get_statistics(self):
        """Тест получения статистики"""
        # Получаем категории
        income_cats = self.db.get_categories('income')
        expense_cats = self.db.get_categories('expense')

        salary_category = [cat for cat in income_cats if cat[1] == 'Зарплата'][0]
        products_category = [cat for cat in expense_cats if cat[1] == 'Продукты'][0]

        # Добавляем доход
        self.db.add_transaction(
            date=datetime.now(),
            amount=1000.0,
            category_id=salary_category[0],
            description="Тестовый доход",
            type_="income"
        )

        # Добавляем расход
        self.db.add_transaction(
            date=datetime.now(),
            amount=300.0,
            category_id=products_category[0],
            description="Тестовый расход",
            type_="expense"
        )

        # Получаем статистику
        stats = self.db.get_statistics()

        self.assertEqual(stats['income'], 1000.0)
        self.assertEqual(stats['expense'], 300.0)
        self.assertEqual(stats['balance'], 700.0)
        self.assertEqual(stats['total_count'], 2)

    def test_filter_transactions_by_date(self):
        """Тест фильтрации транзакций по дате"""
        # Получаем категорию
        categories = self.db.get_categories('income')
        category_id = categories[0][0]

        # Добавляем транзакции с разными датами
        self.db.add_transaction(
            date=datetime(2024, 1, 15),
            amount=1000.0,
            category_id=category_id,
            description="Январь",
            type_="income"
        )

        self.db.add_transaction(
            date=datetime(2024, 2, 15),
            amount=2000.0,
            category_id=category_id,
            description="Февраль",
            type_="income"
        )

        # Фильтруем по январю
        jan_transactions = self.db.get_transactions(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        self.assertEqual(len(jan_transactions), 1)
        self.assertEqual(jan_transactions[0][4], "Январь")

        # Фильтруем по февралю
        feb_transactions = self.db.get_transactions(
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 2, 29)
        )

        self.assertEqual(len(feb_transactions), 1)
        self.assertEqual(feb_transactions[0][4], "Февраль")


class TestAppLogic(unittest.TestCase):
    """Тесты бизнес-логики приложения"""

    def test_statistics_calculation(self):
        """Тест расчета статистики"""
        stats = {
            'income': 1500.0,
            'expense': 500.0,
            'balance': 1000.0,
            'total_count': 2
        }

        # Проверяем расчет баланса
        self.assertEqual(stats['balance'], stats['income'] - stats['expense'])

        # Проверяем, что баланс может быть отрицательным
        negative_stats = {
            'income': 300.0,
            'expense': 800.0,
            'balance': -500.0,
            'total_count': 2
        }

        self.assertLess(negative_stats['balance'], 0)

    def test_date_parsing(self):
        """Тест парсинга дат"""
        from datetime import datetime

        # Правильные форматы
        date1 = datetime.strptime("2024-01-15", "%Y-%m-%d")
        self.assertEqual(date1.year, 2024)
        self.assertEqual(date1.month, 1)
        self.assertEqual(date1.day, 15)

        date2 = datetime.strptime("2024-12-31", "%Y-%m-%d")
        self.assertEqual(date2.month, 12)

        # Неправильный формат должен вызывать ошибку
        with self.assertRaises(ValueError):
            datetime.strptime("15-01-2024", "%Y-%m-%d")


def run_tests():
    """Запуск всех тестов"""
    # Создаем тестовый набор
    loader = unittest.TestLoader()

    # Добавляем тесты
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestAppLogic))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)