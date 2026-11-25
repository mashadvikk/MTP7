import subprocess
import sys

TASKS = {
    "1": ("Средняя 4. Обновить запись", "update_row.py"),
    "2": ("Средняя 6. Параметры запроса", "query_params.py"),
    "3": ("Средняя 10. SQLAlchemy для одной таблицы", "orm_table.py"),
    "4": ("Повышенная 5. Транзакции", "transactions.py"),
    "5": ("Повышенная 9. Асинхронный доступ (databases)", "async_access.py"),
}


def main():
    while True:
        print("\nЛабораторная №7, вариант 4. Задания:")
        for key, (title, _) in TASKS.items():
            print(f"  {key}. {title}")
        print("  0. Выход")
        choice = input("Номер задания: ").strip()
        if choice == "0":
            print("Пока!")
            return
        task = TASKS.get(choice)
        if task is None:
            print("Нет такого пункта, попробуйте ещё раз.")
            continue
        title, script = task
        print(f"--- {title} ---")
        subprocess.run([sys.executable, script], check=False)


if __name__ == "__main__":
    main()
