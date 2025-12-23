import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
from datetime import datetime
from view import FinanceView
from model import FinanceModel


class FinanceController:
    def __init__(self, root):
        self.model = FinanceModel()
        self.view = FinanceView(root)

        self.setup_events()
        self.load_data()

    def setup_events(self):
        """Настройка обработчиков событий"""
        self.view.add_button.config(command=self.open_add_transaction)
        self.view.refresh_button.config(command=self.load_data)
        self.view.filter_button.config(command=self.apply_filter)
        self.view.context_menu.entryconfig("Удалить", command=self.delete_transaction)

    def load_data(self, start_date=None, end_date=None):
        """Загрузка всех данных"""
        # Загрузка транзакций
        transactions = self.model.get_transactions(start_date, end_date)
        self.view.load_transactions(transactions)

        # Обновление названий категорий
        self.update_category_names()

        # Обновление статистики
        stats = self.model.get_statistics(start_date, end_date)
        self.view.update_statistics(stats)

    def update_category_names(self):
        """Обновление названий категорий"""
        category_map = {}
        for cat in self.model.get_categories():
            category_map[cat[0]] = cat[1]

        # Добавляем для None (если категория не указана)
        category_map[None] = "Без категории"

        self.view.update_category_names(category_map)

    def apply_filter(self):
        """Применение фильтра"""
        start_date, end_date = self.view.get_filter_dates()

        if start_date is None and self.view.start_date_entry.get():
            messagebox.showerror("Ошибка", "Неверный формат начальной даты")
            return
        if end_date is None and self.view.end_date_entry.get():
            messagebox.showerror("Ошибка", "Неверный формат конечной даты")
            return

        self.load_data(start_date, end_date)

    def delete_transaction(self):
        """Удаление транзакции"""
        transaction_id = self.view.get_selected_transaction_id()
        if not transaction_id:
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную операцию?"):
            if self.model.delete_transaction(transaction_id):
                self.load_data()
                messagebox.showinfo("Успех", "Операция удалена")

    def open_add_transaction(self):
        """Открытие диалога добавления транзакции"""
        dialog = Toplevel(self.view.root)
        dialog.title("Добавить операцию")
        dialog.geometry("400x350")
        dialog.transient(self.view.root)
        dialog.grab_set()

        # Переменные для формы
        type_var = tk.StringVar(value="expense")
        category_var = tk.StringVar()

        # Загрузка категорий
        categories = self.model.get_categories()

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
                self.model.add_transaction(date, amount, category_id, description, type_)

                # Обновляем интерфейс
                self.load_data()
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

    def close(self):
        """Закрытие приложения"""
        self.model.close()