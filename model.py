import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class FinanceModel:
    def __init__(self, db_name='finance.db'):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Создание таблиц"""
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS categories
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                name
                                TEXT
                                NOT
                                NULL,
                                type
                                TEXT
                                CHECK (
                                type
                                IN
                            (
                                'income',
                                'expense'
                            )) NOT NULL,
                                UNIQUE
                            (
                                name,
                                type
                            )
                                )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS transactions
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                date
                                TEXT
                                NOT
                                NULL,
                                amount
                                REAL
                                NOT
                                NULL,
                                category_id
                                INTEGER,
                                description
                                TEXT,
                                type
                                TEXT
                                CHECK (
                                type
                                IN
                            (
                                'income',
                                'expense'
                            )) NOT NULL
                                )
                            ''')

        self.create_default_categories()
        self.connection.commit()

    def create_default_categories(self):
        """Создание категорий по умолчанию"""
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            income_categories = [
                ('Зарплата', 'income'),
                ('Фриланс', 'income'),
                ('Прочее', 'income')
            ]

            expense_categories = [
                ('Продукты', 'expense'),
                ('Транспорт', 'expense'),
                ('Жилье', 'expense'),
                ('Развлечения', 'expense'),
                ('Прочее', 'expense')
            ]

            for name, type_ in income_categories + expense_categories:
                self.cursor.execute(
                    "INSERT INTO categories (name, type) VALUES (?, ?)",
                    (name, type_)
                )
            self.connection.commit()

    def add_transaction(self, date: datetime, amount: float,
                        category_id: Optional[int], description: str,
                        type_: str) -> int:
        """Добавление транзакции"""
        self.cursor.execute('''
                            INSERT INTO transactions (date, amount, category_id, description, type)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (
                                date.strftime('%Y-%m-%d'),
                                amount,
                                category_id,
                                description,
                                type_
                            ))
        self.connection.commit()
        return self.cursor.lastrowid

    def get_transactions(self, start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Tuple]:
        """Получение транзакций"""
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.strftime('%Y-%m-%d'))

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.strftime('%Y-%m-%d'))

        query += " ORDER BY date DESC"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_categories(self, type_filter: Optional[str] = None) -> List[Tuple]:
        """Получение категорий"""
        query = "SELECT * FROM categories"
        params = []

        if type_filter:
            query += " WHERE type = ?"
            params.append(type_filter)

        query += " ORDER BY name"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_category_name(self, category_id: int) -> str:
        """Получение названия категории"""
        if category_id is None:
            return "Без категории"

        self.cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        result = self.cursor.fetchone()
        return result[0] if result else "Неизвестная категория"

    def get_statistics(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict:
        """Получение статистики"""
        query = '''
                SELECT type, \
                       SUM(amount) as total, \
                       COUNT(*) as count
                FROM transactions
                WHERE 1=1 \
                '''
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.strftime('%Y-%m-%d'))

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.strftime('%Y-%m-%d'))

        query += " GROUP BY type"

        self.cursor.execute(query, params)

        stats = {'income': 0.0, 'expense': 0.0, 'balance': 0.0, 'total_count': 0}
        for row in self.cursor.fetchall():
            type_, total, count = row
            if type_ == 'income':
                stats['income'] = float(total or 0)
            elif type_ == 'expense':
                stats['expense'] = float(total or 0)
            stats['total_count'] += count or 0

        stats['balance'] = stats['income'] - stats['expense']
        return stats

    def delete_transaction(self, transaction_id: int) -> bool:
        """Удаление транзакции"""
        self.cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def close(self):
        """Закрытие соединения"""
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()