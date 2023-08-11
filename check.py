from dateutil import parser
from datetime import datetime, timedelta, date
import locale
import sqlite3
from tabulate import tabulate
from DayBirthdb import DayBirthDB

locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')


class DayBirth(DayBirthDB):
    def __init__(self, db_file):
        super().__init__(db_file)
        self.nearest_diff = None #разница в днях
        self.nearest_employees = [] #список ближайших др

    def read_table(self, table_name):
        try:
            sqlite_select_query = f"SELECT * from {table_name}"
            self.cursor.execute(sqlite_select_query)
            records = self.cursor.fetchall()

            headers = [description[0] for description in self.cursor.description]

            records = records[0:]

            non_empty_records = [row for row in records if any(row)]

            table = tabulate(non_empty_records, headers=headers, tablefmt="grid")

            return table
        except:
            return False

    def search_person_birth(self, surname=None, firstname=None, patronymic=None):
        try:
            if surname:
                query = "SELECT column1, column2 FROM DayBirth1 WHERE column1 LIKE ?"
                self.cursor.execute(query, (f"%{surname}%",))
            else:
                return None

            results = self.cursor.fetchall()

            if results:
                employees = []
                for result in results:
                    name, birthday = result
                    employees.append((name, parser.parse(birthday).strftime("%d %B %Y")))

                return employees
            else:
                return None

        except:
            return False

    def add_employee_birth(self, new_employee_name, new_birth_date):
        try:
            query = "INSERT INTO DayBirth1 (`column1`, `column2`) VALUES (?, ?)"
            self.cursor.execute(query, (new_employee_name, new_birth_date))
            self.connection.commit()
            return True
        except:
            return False

    def remove_employee_birth(self, employee_name):
        try:
            query = "DELETE FROM DayBirth1 WHERE `column1` = ?"
            self.cursor.execute(query, (employee_name,))
            self.connection.commit()
            return True
        except:
            return False

    # def update_birthdates(self):
    #     query = "UPDATE DayBirth1 SET column2 = strftime('%m/%d/%Y', column2)"
    #     self.cursor.execute(query)
    #     self.connection.commit()
    #     print("Даты рождения успешно обновлены.")

    def find_nearest_birthday(self):
        current_date = datetime.now().date()
        query = """
            SELECT column1, column2, DATE(column2) AS formatted_birthday,
            (julianday(DATE(column2)) - julianday('now')) AS diff_days
            FROM DayBirth1
            WHERE column2 IS NOT NULL AND column2 <> 'Дата рождения'
            ORDER BY ABS(diff_days) ASC"""

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        if results:
            self.nearest_diff = None
            self.nearest_employees = []

            for result in results:
                name, birthday, formatted_birthday, diff_days = result
                try:
                    birthday_datetime = datetime.strptime(birthday, "%m/%d/%Y")
                    birthday_date = birthday_datetime.date()

                    next_birthday = datetime(current_date.year, birthday_date.month, birthday_date.day).date()

                    if next_birthday < current_date:
                        next_birthday = datetime(current_date.year + 1, birthday_date.month,
                                                 birthday_date.day).date()

                    diff = (next_birthday - current_date).days
                    formatted_birthday = next_birthday.strftime("%d %B %Y")

                    if diff == 1 or diff == 0:
                        if self.nearest_diff is None or diff < self.nearest_diff:
                            self.nearest_diff = diff
                            self.nearest_employees = [(name, formatted_birthday, birthday, diff)]
                        elif diff == self.nearest_diff:
                            self.nearest_employees.append((name, formatted_birthday, birthday, diff))

                except ValueError:
                    return False

        else:
            self.nearest_diff = None
            self.nearest_employees = []

    def print_nearest_employees(self):
        if self.nearest_employees:
            print("Сотрудники с ближайшей датой рождения:")
            for employee in self.nearest_employees:
                name, formatted_birthday, birthday, diff = employee

                print("Сотрудник: {}\n"
                      "Ближайший день рождения: {}\n"
                      "Дата рождения: {}\n"
                      "Осталось дней: {}\n".format(name, formatted_birthday, birthday, diff))
        else:
            print("Нет данных о сотрудниках с ближайшей датой рождения.")


db = DayBirth('DayBirth.db')

#db.remove_employee_birth("Руденко Елена Дмитриевна")
#db.add_employee_birth("Николайчик Анна Эдуардовна","07/12/1989")
#db.find_nearest_birthday()
#db.print_nearest_employees()
#db.close_connection()
