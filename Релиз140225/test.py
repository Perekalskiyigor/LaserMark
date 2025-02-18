import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Функции-заглушки для кнопок
def load_template():
    pass

def setTamplate():
    pass

def execute_command():
    pass

def start_cutting():
    pass

# Основное окно
root = tk.Tk()
root.title("Система управления")
root.geometry("800x850")  # Увеличиваем ширину окна для колонки слева

# Создаем вкладки
tab_control = ttk.Notebook(root)
tab_main = ttk.Frame(tab_control)
tab_about = ttk.Frame(tab_control)

# Добавляем вкладки в контроль
tab_control.add(tab_main, text="Главная")
tab_control.add(tab_about, text="О программе")
tab_control.pack(side="right", expand=1, fill="both")  # Переносим вкладки на правую сторону

# Создаем левую панель для кнопок
left_panel = tk.Frame(root, width=150, bg="lightgray")  # Панель слева
left_panel.pack(side="left", fill="y")  # Заполняем по высоте

# Добавляем кнопки в левую панель
button_left_1 = tk.Button(left_panel, text="Кнопка 1", command=load_template)
button_left_1.pack(pady=5)

button_left_2 = tk.Button(left_panel, text="Кнопка 2", command=setTamplate)
button_left_2.pack(pady=5)

button_left_3 = tk.Button(left_panel, text="Кнопка 3", command=execute_command)
button_left_3.pack(pady=5)

button_left_4 = tk.Button(left_panel, text="Кнопка 4", command=start_cutting)
button_left_4.pack(pady=5)

# Вкладка "Главная"
# Загружаем логотип
logo = Image.open("logo.png")  # Замените на путь к своему логотипу
logo = logo.resize((100, 100), Image.Resampling.LANCZOS)
logo_img = ImageTk.PhotoImage(logo)

# Создаем лейбл для логотипа
logo_label = tk.Label(tab_main, image=logo_img)
logo_label.pack(pady=10)

# Текстовые подсказки
label_title = tk.Label(tab_main, text="Загрузите шаблон и настройте параметры", font=("Arial", 14))
label_title.pack(pady=10)

# Кнопка выбора шаблона
button_select_template = tk.Button(tab_main, text="Выбрать шаблон", command=load_template)
button_select_template.pack(pady=10)

# Метка для отображения выбранного шаблона
template_label = tk.Label(tab_main, text="Шаблон не выбран", font=("Arial", 10))
template_label.pack
