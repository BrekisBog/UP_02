import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta


class FinanceView:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет личных финансов")
        self.root.geometry("1200x700")

        self.create_widgets()

    def create_widgets(self):
        # Панель статистики
        stats_frame = ttk.Frame(self.root, padding="10")
        stats_frame.pack(fill='x')

        self.balance_label = ttk.Label(stats_frame, text="Баланс: 0.00 ₽",
                                       font=('Arial', 14, 'bold'))
        self.balance_label.pack(side='left', padx=20)

        self.income_label = ttk.Label(stats_frame, text="Доходы: 0.00 ₽",
                                      font=('Arial', 12), foreground='green')
        self.income_label.pack(side='left', padx=20)

        self.expense_label = ttk.Label(stats_frame, text="Расходы: 0.00 ₽",
                                       font=('Arial', 12), foreground='red')
        self.expense_label.pack(side='left', padx=20)

        # Панель управления
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill='x')

        self.add_button = ttk.Button(control_frame, text="Добавить операцию")
        self.add_button.pack(side='left', padx=5)

        self.refresh_button = ttk.Button(control_frame, text="Обновить")
        self.refresh_button.pack(side='left', padx=5)

        # Фильтры
        filter_frame = ttk.LabelFrame(control_frame, text="Фильтры", padding="5")
        filter_frame.pack(side='left', padx=20)

        ttk.Label(filter_frame, text="С:").pack(side='left')
        self.start_date_entry = ttk.Entry(filter_frame, width=10)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.start_date_entry.pack(side='left', padx=5)

        ttk.Label(filter_frame, text="По:").pack(side='left')
        self.end_date_entry = ttk.Entry(filter_frame, width=10)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.end_date_entry.pack(side='left', padx=5)

        self.filter_button = ttk.Button(filter_frame, text="Применить фильтр")
        self.filter_button.pack(side='left', padx=5)

        # Таблица транзакций
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.create_transactions_table(table_frame)

    def create_transactions_table(self, parent):
        columns = ('id', 'date', 'amount', 'category', 'description', 'type')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=25)

        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Дата')
        self.tree.heading('amount', text='Сумма')
        self.tree.heading('category', text='Категория')
        self.tree.heading('description', text='Описание')
        self.tree.heading('type', text='Тип')

        self.tree.column('id', width=50)
        self.tree.column('date', width=100)
        self.tree.column('amount', width=100)
        self.tree.column('category', width=150)
        self.tree.column('description', width=400)
        self.tree.column('type', width=80)

        # Прокрутка
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Удалить")
        self.tree.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_transactions(self, transactions):
        """Загрузка транзакций в таблицу"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загрузка данных
        for row in transactions:
            id_, date_str, amount, category_id, description, type_ = row

            tags = ('income',) if type_ == 'income' else ('expense',)

            self.tree.insert('', 'end',
                             values=(
                                 id_,
                                 date_str,
                                 f"{amount:.2f} ₽",
                                 category_id,  # Будет заменено контроллером
                                 description,
                                 "Доход" if type_ == 'income' else "Расход"
                             ),
                             tags=tags
                             )

        self.tree.tag_configure('income', foreground='green')
        self.tree.tag_configure('expense', foreground='red')

    def update_statistics(self, stats):
        """Обновление статистики"""
        self.balance_label.config(
            text=f"Баланс: {stats['balance']:.2f} ₽",
            foreground='blue' if stats['balance'] >= 0 else 'red'
        )
        self.income_label.config(text=f"Доходы: {stats['income']:.2f} ₽")
        self.expense_label.config(text=f"Расходы: {stats['expense']:.2f} ₽")

    def get_selected_transaction_id(self):
        """Получение ID выбранной транзакции"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            return item['values'][0]
        return None

    def get_filter_dates(self):
        """Получение дат фильтра"""
        try:
            start_date = None
            end_date = None

            if self.start_date_entry.get():
                start_date = datetime.strptime(self.start_date_entry.get(), '%Y-%m-%d')

            if self.end_date_entry.get():
                end_date = datetime.strptime(self.end_date_entry.get(), '%Y-%m-%d')

            return start_date, end_date
        except ValueError:
            return None, None

    def update_category_names(self, category_map):
        """Обновление названий категорий в таблице"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            category_id = values[3]
            values[3] = category_map.get(category_id, "Неизвестная категория")
            self.tree.item(item, values=values)