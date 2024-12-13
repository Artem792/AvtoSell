import sys
import sqlite3
from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QStackedWidget, QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QDialog,
    QHeaderView
)


def initialize_database():
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Создаем таблицу cars
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            seller_login TEXT NOT NULL,
            status TEXT DEFAULT 'В продаже',
            buyer_login TEXT,
            date_added TEXT,  -- Поле для даты добавления
            purchase_date TEXT -- Поле для даты покупки
        )
    """)

    # Создаем таблицу users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Проверяем наличие необходимых столбцов в таблице cars
    cursor.execute("PRAGMA table_info(cars)")
    columns = [col[1] for col in cursor.fetchall()]
    if "date_added" not in columns:
        cursor.execute("ALTER TABLE cars ADD COLUMN date_added TEXT")
    if "purchase_date" not in columns:
        cursor.execute("ALTER TABLE cars ADD COLUMN purchase_date TEXT")

    connection.commit()
    connection.close()




class AdminPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Создаем интерфейс для управления пользователями"""
        layout = QVBoxLayout()

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Логин", "Роль"])

        delete_user_button = QPushButton("Удалить пользователя")
        show_cars_button = QPushButton("Показать список машин")
        back_button = QPushButton("Выход")

        delete_user_button.clicked.connect(self.delete_user)
        show_cars_button.clicked.connect(self.show_cars_list)
        back_button.clicked.connect(self.parent.show_login_window)

        layout.addWidget(self.users_table)
        layout.addWidget(delete_user_button)
        layout.addWidget(show_cars_button)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def load_users(self):
        self.users_table.setRowCount(0)

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT id, login, role FROM users")
        users = cursor.fetchall()
        connection.close()

        for row_num, user in enumerate(users):
            self.users_table.insertRow(row_num)
            for col_num, value in enumerate(user):
                self.users_table.setItem(row_num, col_num, QTableWidgetItem(str(value)))

    def delete_user(self):
        selected_row = self.users_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления.")
            return

        user_id = self.users_table.item(selected_row, 0).text()
        user_role = self.users_table.item(selected_row, 2).text()

        if user_id == str(self.parent.current_user[0]):
            QMessageBox.warning(self, "Ошибка", "Вы не можете удалить себя!")
            return
        if user_role == "Админ":
            QMessageBox.warning(self, "Ошибка", "Невозможно удалить админа!")
            return

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        connection.commit()
        connection.close()

        self.load_users()
        QMessageBox.information(self, "Успех", "Пользователь успешно удалён!")

    def show_cars_list(self):
        self.parent.admin_cars_window.load_car_list()
        self.parent.central_widget.setCurrentWidget(self.parent.admin_cars_window)
        self.parent.setWindowTitle("Список машин")


class AdminCarsWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Таблица для списка машин
        self.car_list_table = QTableWidget()
        self.car_list_table.setColumnCount(9)  # Количество столбцов
        self.car_list_table.setHorizontalHeaderLabels([
            "ID", "Марка", "Модель", "Год", "Цена", "Описание", "Продавец", "Статус","Дата добавления"
        ])
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Автоматическое растягивание столбцов
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Устанавливаем минимальные ширины для столбцов
        self.car_list_table.setColumnWidth(0, 50)  # ID
        self.car_list_table.setColumnWidth(1, 150)  # Марка
        self.car_list_table.setColumnWidth(2, 150)  # Модель
        self.car_list_table.setColumnWidth(4, 100)  # Цена
        self.car_list_table.setColumnWidth(8, 150)  # Дата добавления

        # Кнопки "Удалить машину" и "Назад"
        delete_car_button = QPushButton("Удалить машину")
        delete_car_button.clicked.connect(self.delete_car)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.parent.show_admin_panel)

        # Добавляем все элементы в layout
        layout.addWidget(self.car_list_table)
        layout.addWidget(delete_car_button)
        layout.addWidget(back_button)

        self.setLayout(layout)

        # Загружаем список машин
        self.load_car_list()

    def load_car_list(self):
        self.car_list_table.setRowCount(0)

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, make, model, year, price, description, seller_login, status, date_added, purchase_date
            FROM cars
        """)
        cars = cursor.fetchall()
        connection.close()

        for row_num, car in enumerate(cars):
            self.car_list_table.insertRow(row_num)
            for col_num, value in enumerate(car):
                if col_num == 4:  # Цена
                    value = f"{value:.2f} руб."
                elif col_num == 8 and value:  # Дата добавления
                    value = f"{value}"  # Показываем дату добавления
                elif col_num == 9 and value:  # Дата покупки
                    value = f"Куплено ({car[6]}) в {value}"  # Покупатель и дата покупки
                self.car_list_table.setItem(row_num, col_num, QTableWidgetItem(str(value)))

        self.car_list_table.resizeColumnsToContents()

    def delete_car(self):
        selected_row = self.car_list_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите машину для удаления.")
            return

        car_id = self.car_list_table.item(selected_row, 0).text()

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        connection.commit()
        connection.close()

        QMessageBox.information(self, "Успех", "Машина успешно удалена!")
        self.load_car_list()




class SellerPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.car_list_table = QTableWidget()
        self.car_list_table.setColumnCount(9)  # Количество столбцов
        self.car_list_table.setHorizontalHeaderLabels([
            "ID", "Марка", "Модель", "Год", "Цена", "Описание", "Продавец", "Статус","Дата добавления"
        ])
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Автоматическое растягивание столбцов
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Устанавливаем минимальные ширины для столбцов
        self.car_list_table.setColumnWidth(0, 50)  # ID
        self.car_list_table.setColumnWidth(1, 150)  # Марка
        self.car_list_table.setColumnWidth(2, 150)  # Модель
        self.car_list_table.setColumnWidth(4, 100)  # Цена
        self.car_list_table.setColumnWidth(8, 150)  # Дата добавления

        add_car_button = QPushButton("Добавить машину")
        delete_car_button = QPushButton("Удалить машину")
        back_button = QPushButton("Выход")

        add_car_button.clicked.connect(self.show_add_car_window)
        delete_car_button.clicked.connect(self.delete_car)
        back_button.clicked.connect(self.parent.show_login_window)

        layout.addWidget(self.car_list_table)
        layout.addWidget(add_car_button)
        layout.addWidget(delete_car_button)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def load_car_list(self):
        self.car_list_table.setRowCount(0)

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, make, model, year, price, description, seller_login, status, date_added
            FROM cars
        """)
        cars = cursor.fetchall()
        connection.close()

        for row_num, car in enumerate(cars):
            self.car_list_table.insertRow(row_num)
            for col_num, value in enumerate(car):
                if col_num == 4:  # Цена
                    value = f"{value:.2f} руб."
                elif col_num == 8:  # Дата добавления
                    value = f"Машина выставлена на продажу в {value}"

                self.car_list_table.setItem(row_num, col_num, QTableWidgetItem(str(value)))

        self.car_list_table.resizeColumnsToContents()

    def delete_car(self):
        selected_row = self.car_list_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите машину для удаления.")
            return

        car_id = self.car_list_table.item(selected_row, 0).text()

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT seller_login FROM cars WHERE id = ?", (car_id,))
        car = cursor.fetchone()
        connection.close()

        # Проверяем, является ли текущий пользователь продавцом этой машины
        if car and car[0] != self.parent.current_user[1]:
            QMessageBox.warning(self, "Ошибка", "Вы не можете удалить машину другого продавца!")
            return

        # Если это его машина, удаляем
        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        connection.commit()
        connection.close()

        self.load_car_list()
        self.parent.buyer_panel.load_car_list()
        QMessageBox.information(self, "Успех", "Машина успешно удалена!")

    def show_add_car_window(self):
        self.add_car_window = AddCarWindow(self)
        self.add_car_window.show()



class BuyerPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.min_price_input = QLineEdit()
        self.min_price_input.setPlaceholderText("Мин. цена")
        self.max_price_input = QLineEdit()
        self.max_price_input.setPlaceholderText("Макс. цена")
        self.make_input = QLineEdit()
        self.make_input.setPlaceholderText("Марка автомобиля")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Без сортировки", "Цена: по возрастанию", "Цена: по убыванию"])

        apply_filters_button = QPushButton("Применить фильтры")
        apply_filters_button.clicked.connect(self.apply_filters)

        filters_layout = QVBoxLayout()
        filters_layout.addWidget(QLabel("Фильтры"))
        filters_layout.addWidget(self.make_input)
        filters_layout.addWidget(self.min_price_input)
        filters_layout.addWidget(self.max_price_input)
        filters_layout.addWidget(QLabel("Сортировка"))
        filters_layout.addWidget(self.sort_combo)
        filters_layout.addWidget(apply_filters_button)

        self.car_list_table = QTableWidget()
        self.car_list_table.setColumnCount(9)  # Количество столбцов
        self.car_list_table.setHorizontalHeaderLabels([
            "ID", "Марка", "Модель", "Год", "Цена", "Описание", "Продавец", "Статус", "Дата добавления"
        ])
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Автоматическое растягивание столбцов
        self.car_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Устанавливаем минимальные ширины для столбцов
        self.car_list_table.setColumnWidth(0, 50)  # ID
        self.car_list_table.setColumnWidth(1, 150)  # Марка
        self.car_list_table.setColumnWidth(2, 150)  # Модель
        self.car_list_table.setColumnWidth(4, 100)  # Цена
        self.car_list_table.setColumnWidth(8, 150)  # Дата добавления


        buy_car_button = QPushButton("Купить машину")
        buy_car_button.clicked.connect(self.buy_car)

        back_button = QPushButton("Выход")
        back_button.clicked.connect(self.parent.show_login_window)

        layout.addLayout(filters_layout)
        layout.addWidget(self.car_list_table)
        layout.addWidget(buy_car_button)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def load_car_list(self):
        self.car_list_table.setRowCount(0)

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, make, model, year, price, description, seller_login, status, date_added
            FROM cars
        """)
        cars = cursor.fetchall()
        connection.close()

        for row_num, car in enumerate(cars):
            self.car_list_table.insertRow(row_num)
            for col_num, value in enumerate(car):
                if col_num == 4:  # Цена
                    value = f"{value:.2f} руб."
                elif col_num == 8:  # Дата добавления
                    value = f"Машина выставлена на продажу в {value}"

                self.car_list_table.setItem(row_num, col_num, QTableWidgetItem(str(value)))

        self.car_list_table.resizeColumnsToContents()

    def apply_filters(self):
        self.car_list_table.setRowCount(0)
        query = """
                SELECT id, make, model, year, price, description, seller_login, status, date_added
                FROM cars
                WHERE 1=1
            """
        params = []

        make = self.make_input.text()
        if make:
            query += " AND make LIKE ?"
            params.append(f"%{make}%")

        if self.min_price_input.text():
            query += " AND price >= ?"
            params.append(float(self.min_price_input.text()))

        if self.max_price_input.text():
            query += " AND price <= ?"
            params.append(float(self.max_price_input.text()))

        if self.sort_combo.currentText() == "Цена: по возрастанию":
            query += " ORDER BY price ASC"
        elif self.sort_combo.currentText() == "Цена: по убыванию":
            query += " ORDER BY price DESC"

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute(query, params)
        cars = cursor.fetchall()
        connection.close()

        for row_num, car in enumerate(cars):
            self.car_list_table.insertRow(row_num)
            self.car_list_table.setRowHeight(row_num, 100)
            for col_num, value in enumerate(car):
                if col_num == 4:  # Цена
                    value = f"{value:.2f} руб."
                elif col_num == 8:  # Дата добавления
                    # Включаем дату и время
                    value = f"Машина выставлена на продажу: {value}"  # Предполагается, что value уже содержит дату и время
                elif col_num == 7:  # Статус
                    if "Куплено" in value:  # Если машина куплена
                        status_parts = value.split(' в ')
                        date_time = status_parts[1] if len(status_parts) > 1 else ""
                        value = f"Куплено {status_parts[0]} в {date_time}"  # Форматируем с временем

                self.car_list_table.setItem(row_num, col_num, QTableWidgetItem(str(value)))

        if not cars:
            QMessageBox.warning(self, "Нет данных", "По вашему запросу ничего не найдено.")

    def buy_car(self):
        selected_row = self.car_list_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите машину для покупки.")
            return

        car_id = self.car_list_table.item(selected_row, 0).text()
        buyer_login = self.parent.current_user[1]

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT buyer_login FROM cars WHERE id = ?", (car_id,))
        existing_buyer = cursor.fetchone()
        connection.close()

        if existing_buyer and existing_buyer[0] == buyer_login:
            QMessageBox.warning(self, "Ошибка", "Вы уже купили эту машину!")
            return

        purchase_datetime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")  # Форматируем дату и время

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE cars
            SET status = ?, buyer_login = ?, purchase_date = ?
            WHERE id = ?
        """, (f"Куплено ({buyer_login}) в {purchase_datetime}", buyer_login, purchase_datetime, car_id))
        connection.commit()
        connection.close()

        self.load_car_list()
        QMessageBox.information(self, "Успех", "Машина успешно куплена!")


class AddCarWindow(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Добавить машину")

        self.make_input = QLineEdit(self)
        self.make_input.setPlaceholderText("Введите марку автомобиля")

        self.model_input = QLineEdit(self)
        self.model_input.setPlaceholderText("Введите модель автомобиля")

        self.year_input = QLineEdit(self)
        self.year_input.setPlaceholderText("Введите год выпуска")

        self.price_input = QLineEdit(self)
        self.price_input.setInputMask("000000000.00 руб")  # Маска ввода: неизменяемая точка и "руб"
        self.price_input.setText("0.00 руб")  # Устанавливаем начальное значение
        self.price_input.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Текст выравнивается влево
        self.price_input.setCursorPosition(0)

        self.price_input.setReadOnly(False)  # Поле остается редактируемым
        self.price_input.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Устанавливаем выравнивание влево

        # Устанавливаем фильтр событий для управления текстом
        self.price_input.installEventFilter(self)

        self.description_input = QTextEdit(self)
        self.description_input.setPlaceholderText("Введите описание машины")
        self.description_input.setMaximumHeight(100)

        self.add_button = QPushButton("Добавить", self)
        self.add_button.clicked.connect(self.add_car)

        layout = QVBoxLayout(self)
        layout.addWidget(self.make_input)
        layout.addWidget(self.model_input)
        layout.addWidget(self.year_input)
        layout.addWidget(self.price_input)
        layout.addWidget(self.description_input)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        self.price_input.installEventFilter(self)
    def eventFilter(self, obj, event):
        if obj == self.price_input and event.type() == event.Type.KeyPress:
            cursor_position = self.price_input.cursorPosition()
            text = self.price_input.text()

            # Убираем фиксированное "руб" временно для редактирования
            if text.endswith(" руб"):
                text = text[:-4]  # Убираем " руб"

            # Пропускаем событие клавиши в поле
            result = super().eventFilter(obj, event)

            # Возвращаем " руб" после редактирования
            if text.replace(".", "").isdigit() or text == "":
                self.price_input.setText(text + " руб")
                self.price_input.setCursorPosition(cursor_position)

            return result
        return super().eventFilter(obj, event)

    def add_car(self):
        make = self.make_input.text()
        model = self.model_input.text()
        try:
            year = int(self.year_input.text())
            if year < 1950 or year > 2024:
                QMessageBox.warning(self, "Ошибка", "Год выпуска должен быть от 1950 до 2024.")
                return
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректный год!")
            return

        price_text = self.price_input.text().replace(" руб", "").strip()
        try:
            price = float(price_text)
            if price <= 0:
                QMessageBox.warning(self, "Ошибка", "Цена должна быть положительным числом.")
                return
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную цену!")
            return

        date_added = datetime.now().strftime("%d.%m.%Y %H:%M:%S")  # Форматируем текущую дату
        seller_login = self.parent.parent.current_user[1]

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO cars (make, model, year, price, description, seller_login, date_added, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'В продаже')
        """, (make, model, year, price, self.description_input.toPlainText(), seller_login, date_added))
        connection.commit()
        connection.close()

        QMessageBox.information(self, "Успех", "Машина успешно добавлена!")
        self.parent.load_car_list()
        self.close()


class AuthRegApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setGeometry(300, 300, 300, 200)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.login_widget = self.create_login_window()
        self.central_widget.addWidget(self.login_widget)

        self.register_widget = self.create_register_window()
        self.central_widget.addWidget(self.register_widget)

        self.admin_panel = AdminPanel(self)
        self.central_widget.addWidget(self.admin_panel)

        self.admin_cars_window = AdminCarsWindow(self)  # Новый экран
        self.central_widget.addWidget(self.admin_cars_window)

        self.seller_panel = SellerPanel(self)
        self.central_widget.addWidget(self.seller_panel)

        self.add_car_window = AddCarWindow(self)
        self.central_widget.addWidget(self.add_car_window)

        self.buyer_panel = BuyerPanel(self)
        self.central_widget.addWidget(self.buyer_panel)

        self.current_user = None

    def show_admin_panel(self):
        self.central_widget.setCurrentWidget(self.admin_panel)

    def create_login_window(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)


        self.login_input.returnPressed.connect(self.focus_on_password)
        self.password_input.returnPressed.connect(self.focus_on_login)

        login_button = QPushButton("Войти")
        register_button = QPushButton("Зарегистрироваться")

        login_button.clicked.connect(self.login)
        register_button.clicked.connect(self.show_register_window)

        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(register_button)

        widget.setLayout(layout)
        return widget

    def focus_on_password(self):
        self.password_input.setFocus()

    def focus_on_login(self):
        self.login_input.setFocus()

    def create_register_window(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.reg_login_input = QLineEdit()
        self.reg_login_input.setPlaceholderText("Логин")
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setPlaceholderText("Пароль")
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Админ", "Продавец", "Покупатель"])

        register_button = QPushButton("Зарегистрироваться")
        back_button = QPushButton("Назад")

        register_button.clicked.connect(self.register)
        back_button.clicked.connect(self.show_login_window)

        layout.addWidget(self.reg_login_input)
        layout.addWidget(self.reg_password_input)
        layout.addWidget(QLabel("Выберите роль"))
        layout.addWidget(self.role_combo)
        layout.addWidget(register_button)
        layout.addWidget(back_button)

        widget.setLayout(layout)
        return widget

    def login(self):
        login = self.login_input.text()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль!")
            return

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        cursor.execute("SELECT id, login, password, role FROM users WHERE login = ?", (login,))
        user = cursor.fetchone()
        connection.close()

        if user and user[2] == password:
            self.current_user = user
            role = user[3]
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {role}!")
            if role == "Админ":
                self.setWindowTitle("Окно администратора")
                self.admin_panel.load_users()
                self.central_widget.setCurrentWidget(self.admin_panel)
            elif role == "Продавец":
                self.setWindowTitle("Окно продавца")
                self.seller_panel.load_car_list()
                self.central_widget.setCurrentWidget(self.seller_panel)
            elif role == "Покупатель":
                self.setWindowTitle("Окно покупателя")
                self.buyer_panel.load_car_list()
                self.central_widget.setCurrentWidget(self.buyer_panel)
            else:
                self.show_login_window()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")

    def register(self):
        login = self.reg_login_input.text()
        password = self.reg_password_input.text()
        role = self.role_combo.currentText()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль!")
            return

        if len(login) > 10:
            QMessageBox.warning(self, "Ошибка", "Логин не должен превышать 10 символов!")
            return

        if len(password) > 8:
            QMessageBox.warning(self, "Ошибка", "Пароль не должен превышать 8 символов!")
            return

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (login, password, role) VALUES (?, ?, ?)",
                           (login, password, role))
            connection.commit()
            QMessageBox.information(self, "Успех", "Пользователь зарегистрирован!")
            self.show_login_window()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Этот логин уже существует!")
        finally:
            connection.close()

    def show_login_window(self):
        self.setWindowTitle("Авторизация")
        self.central_widget.setCurrentWidget(self.login_widget)
    def show_register_window(self):
        self.setWindowTitle("Регистрация")
        self.central_widget.setCurrentWidget(self.register_widget)

    def show_add_car_window(self):
        self.central_widget.setCurrentWidget(self.add_car_window)

    def show_cars_list(self):
        self.parent.admin_cars_window.load_car_list()
        self.parent.central_widget.setCurrentWidget(self.parent.admin_cars_window)
        self.parent.setWindowTitle("Список машин")


def main():
    app = QApplication(sys.argv)
    initialize_database()
    window = AuthRegApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
