import requests
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from io import BytesIO

# SPARQL ендпоінт DBpedia
endpoint = "https://dbpedia.org/sparql"

PAGE_SIZE = 10
offset = 0 

def get_sparql_query(offset, limit):
    return f"""
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbr: <http://dbpedia.org/resource/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?city ?cityLabel ?population ?coordinates ?image ?abstract ?country WHERE {{
      ?city dbo:country dbr:Ukraine .
      ?city a dbo:City .
      ?city rdfs:label ?cityLabel .
      OPTIONAL {{ ?city dbo:populationTotal ?population . }}
      OPTIONAL {{ ?city dbo:coordinates ?coordinates . }}
      OPTIONAL {{ ?city dbo:thumbnail ?image . }}
      OPTIONAL {{ ?city dbo:abstract ?abstract . }}
      OPTIONAL {{ ?city dbo:country ?country . }}
      FILTER(LANG(?cityLabel) = 'uk')
      FILTER(LANG(?abstract) = 'uk')
    }}
    ORDER BY ?cityLabel
    OFFSET {offset}
    LIMIT {limit}
    """

# Функція для виконання SPARQL-запиту
def execute_sparql_query(query):
    response = requests.get(endpoint, params={'query': query, 'format': 'json'})
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Функція для завантаження і відображення зображення
def fetch_image(image_url):
    try:
        if image_url:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            img_response = requests.get(image_url, headers=headers)

            if img_response.status_code == 200:
                if 'image' in img_response.headers.get('Content-Type', ''):
                    img = Image.open(BytesIO(img_response.content))
                    img = img.resize((400, 400))  # Масштабування зображення до 400x400
                    return ImageTk.PhotoImage(img)
                else:
                    return None
            elif img_response.status_code == 403:
                print(f"Доступ до зображення за URL {image_url} заборонено (403).")
                return None
            else:
                return None
        return None
    except Exception as e:
        print(f"Помилка при завантаженні зображення: {e}")
        return None

# Створення вікна
root = tk.Tk()
root.title("Гід містами України")
root.geometry("800x800")  # Збільшено розмір вікна
root.config(bg="#f0f0f0")

header_label = tk.Label(root, text="Гід містами України", font=("Helvetica", 24, "bold"), bg="#f0f0f0", fg="#333")
header_label.pack(pady=20)

# Кнопка для отримання даних
cities_data = []  # Змінна для зберігання інформації про міста
current_city_index = 0  # Індекс поточного міста

def display_city_info():
    global cities_data, offset
    query = get_sparql_query(offset, PAGE_SIZE)
    data = execute_sparql_query(query)
    
    if data:
        new_cities = data['results']['bindings']
        if new_cities:
            cities_data.extend(new_cities)
            show_city(current_city_index)
            offset += PAGE_SIZE  # Оновлення зсуву для наступного запиту
        else:
            messagebox.showinfo("Результат", "Не знайдено більше міст.")
    else:
        messagebox.showerror("Помилка", "Не вдалося отримати дані.")

# Функція для відображення інформації про місто
def show_city(index):
    global cities_data
    if 0 <= index < len(cities_data):
        city = cities_data[index]
        city_name = city['cityLabel']['value']
        population = city.get('population', {}).get('value', 'Немає даних')
        coordinates = city.get('coordinates', {}).get('value', 'Немає даних')
        image_url = city.get('image', {}).get('value', None)
        abstract = city.get('abstract', {}).get('value', 'Немає додаткової інформації')
        country = city.get('country', {}).get('value', 'Немає даних про країну')

        city_info = f"{city_name}\nНаселення: {population}\nКоординати: {coordinates}\nКраїна: {country}\n\nОпис:\n{abstract}"
        info_text.delete(1.0, tk.END)  # Очистити попередній текст
        info_text.insert(tk.END, city_info)  # Вставити новий текст

        city_image = fetch_image(image_url)
        if city_image:
            image_label.config(image=city_image)
            image_label.image = city_image  # Зберігаємо посилання на зображення
        else:
            image_label.config(image=None)
    else:
        messagebox.showinfo("Результат", "Більше міст немає.")

# Кнопка "Далі"
def next_city():
    global current_city_index
    current_city_index += 1
    if current_city_index < len(cities_data):
        show_city(current_city_index)
    else:
        messagebox.showinfo("Результат", "Ви переглянули всі міста.")

# Кнопка для завантаження більше міст
def load_more_cities():
    display_city_info()

# Кнопка для запуску програми
button = tk.Button(root, text="Отримати інформацію про міста", command=display_city_info, font=("Helvetica", 14), bg="#4CAF50", fg="white", padx=20, pady=10, relief="flat")
button.pack(pady=10)

info_frame = tk.Frame(root)
info_frame.pack(pady=20)

scrollbar = tk.Scrollbar(info_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

info_text = tk.Text(info_frame, font=("Helvetica", 12), bg="#f0f0f0", fg="#333", wrap=tk.WORD, height=10, width=75)
info_text.pack(padx=20, pady=20)
info_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=info_text.yview)

# Рамка для відображення зображення
image_label = tk.Label(root, bd=5, relief="solid")
image_label.pack(pady=20)

# Кнопка "Далі"
next_button = tk.Button(root, text="Далі", command=next_city, font=("Helvetica", 14), bg="#2196F3", fg="white", padx=20, pady=10, relief="flat")
next_button.pack(pady=10)

# Кнопка для завантаження більше міст
load_more_button = tk.Button(root, text="Завантажити більше міст", command=load_more_cities, font=("Helvetica", 14), bg="#FF9800", fg="white", padx=20, pady=10, relief="flat")
load_more_button.pack(pady=10)

# Запуск головного циклу програми
root.mainloop()
