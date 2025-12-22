import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from database import Database


class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет личных финансов")
        self.root.geometry("1200x700")

        self.db = Database()

        self.create_widgets()
        self.load_transactions()

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

        ttk.Button(control_frame, text="Добавить операцию",
                   command=self.open_add_transaction).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Обновить",
                   command=self.load_transactions).pack(side='left', padx=5)

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

        ttk.Button(filter_frame, text="Применить фильтр",
                   command=self.apply_filter).pack(side='left', padx=5)

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
        self.context_menu.add_command(label="Удалить", command=self.delete_selected_transaction)
        self.tree.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_transaction(self):
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную операцию?"):
            item = self.tree.item(selected[0])
            transaction_id = item['values'][0]

            self.db.delete_transaction(transaction_id)
            self.load_transactions()
            messagebox.showinfo("Успех", "Операция удалена")

    def load_transactions(self, start_date=None, end_date=None):
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загрузка данных
        transactions = self.db.get_transactions(start_date, end_date)

        for row in transactions:
            id_, date_str, amount, category_id, description, type_, created_at = row
            category_name = self.db.get_category_name(category_id)

            tags = ('income',) if type_ == 'income' else ('expense',)

            self.tree.insert('', 'end',
                             values=(
                                 id_,
                                 datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y'),
                                 f"{amount:.2f} ₽",
                                 category_name,
                                 description,
                                 "Доход" if type_ == 'income' else "Расход"
                             ),
                             tags=tags
                             )

        self.tree.tag_configure('income', foreground='green')
        self.tree.tag_configure('expense', foreground='red')

        # Обновление статистики
        self.update_statistics(start_date, end_date)

    def update_statistics(self, start_date=None, end_date=None):
        stats = self.db.get_statistics(start_date, end_date)

        self.balance_label.config(
            text=f"Баланс: {stats['balance']:.2f} ₽",
            foreground='blue' if stats['balance'] >= 0 else 'red'
        )
        self.income_label.config(text=f"Доходы: {stats['income']:.2f} ₽")
        self.expense_label.config(text=f"Расходы: {stats['expense']:.2f} ₽")

    def apply_filter(self):
        try:
            start_date = None
            end_date = None

            if self.start_date_entry.get():
                start_date = datetime.strptime(self.start_date_entry.get(), '%Y-%m-%d')

            if self.end_date_entry.get():
                end_date = datetime.strptime(self.end_date_entry.get(), '%Y-%m-%d')

            self.load_transactions(start_date, end_date)

        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")

    def open_add_transaction(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить операцию")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()

        # Переменные для формы
        type_var = tk.StringVar(value="expense")
        category_var = tk.StringVar()

        # Загрузка категорий
        categories = self.db.get_categories()

        # Элементы формы
        ttk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        date_entry = ttk.Entry(dialog)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(dialog, text="Тип:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        type_combo = ttk.Combobox(dialog, textvariable=type_var,
                                  values=['income', 'expense'], state='readonly', width=18)
        type_combo.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        def update_categories():
            type_ = type_var.get()
            filtered_categories = [cat for cat in categories if cat[2] == type_]
            category_names = [cat[1] for cat in filtered_categories]
            category_combo['values'] = category_names
            if category_names:
                category_combo.set(category_names[0])

        type_combo.bind('<<ComboboxSelected>>', lambda e: update_categories())

        ttk.Label(dialog, text="Категория:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        category_combo = ttk.Combobox(dialog, textvariable=category_var, width=18)
        category_combo.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(dialog, text="Сумма:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        amount_entry = ttk.Entry(dialog)
        amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(dialog, text="Описание:").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        description_entry = ttk.Entry(dialog)
        description_entry.grid(row=4, column=1, padx=5, pady=5, sticky='ew')

        # Инициализация категорий
        update_categories()

        def save_transaction():
            try:
                # Валидация данных
                date_str = date_entry.get()
                date = datetime.strptime(date_str, '%Y-%m-%d')

                amount_str = amount_entry.get()
                if not amount_str:
                    raise ValueError("Введите сумму")

                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("Сумма должна быть положительной")

                description = description_entry.get().strip()
                if not description:
                    raise ValueError("Введите описание")

                type_ = type_var.get()
                category_name = category_var.get()

                # Получаем ID категории
                category_id = None
                for cat in categories:
                    if cat[1] == category_name and cat[2] == type_:
                        category_id = cat[0]
                        break

                if not category_id:
                    raise ValueError("Выберите категорию")

                # Сохраняем транзакцию
                self.db.add_transaction(date, amount, category_id, description, type_)

                # Обновляем интерфейс
                self.load_transactions()
                dialog.destroy()

                messagebox.showinfo("Успех", "Операция успешно добавлена")

            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Сохранить",
                   command=save_transaction, width=15).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Отмена",
                   command=dialog.destroy, width=15).pack(side='left', padx=10)

        # Настройка сетки
        dialog.columnconfigure(1, weight=1)

    def on_closing(self):
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = FinanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()