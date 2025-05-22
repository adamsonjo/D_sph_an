import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import os

# Загружаем необходимые ресурсы
nltk.download('punkt')
nltk.download('stopwords')

# Функция для чтения данных из файла
def read_sid_phrases(file_path):
    """Чтение фраз из одного файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sid_phrases = file.readlines()
        return [phrase.strip() for phrase in sid_phrases]  # Убираем лишние пробелы и символы новой строки
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return []

# Функция для чтения всех файлов из директории
def read_multiple_files(directory_path):
    """Чтение всех файлов в указанной директории."""
    sid_phrases = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):  # Можно изменить на другой формат, если нужно
            file_path = os.path.join(directory_path, filename)
            sid_phrases.extend(read_sid_phrases(file_path))
    return sid_phrases

# Пример пути к директории с файлами
directory_path = 'C:\\Users\\Пользователь\\Desktop\\Python Projects\\Data Analyze\\seed_phrases'  # Замените на путь к вашей директории с файлами

# Чтение данных из всех файлов в директории
sid_phrases = read_multiple_files(directory_path)

# Проверка, если фразы не загружены
if not sid_phrases:
    print("Не удалось загрузить данные. Проверьте путь к файлам.")
    exit()

# Предобработка текста: токенизация, удаление стоп-слов и пунктуации
def preprocess_text(text):
    """Токенизация текста, удаление стоп-слов и символов."""
    stop_words = set(stopwords.words('english'))  # Стоп-слова для английского языка
    tokens = word_tokenize(text.lower())  # Преобразуем текст в токены (слова)
    tokens = [word for word in tokens if word.isalpha() and word not in stop_words]  # Оставляем только слова (без цифр и пунктуации)
    return tokens

# Обрабатываем все строки (каждая строка — это отдельная фраза или последовательность слов)
all_tokens = []
for phrase in sid_phrases:
    all_tokens.extend(preprocess_text(phrase))

# Частотный анализ слов
word_counts = Counter(all_tokens)

# Создание списка всех уникальных слов
vocab = list(word_counts.keys())

# Создание словаря для отображения индексов слов
word_to_index = {word: index for index, word in enumerate(vocab)}

# Инициализация совместной матрицы частоты
window_size = 5  # Размер окна для подсчета совместной частоты слов
co_occurrence_matrix = np.zeros((len(vocab), len(vocab)))

# Подсчет совместных частот слов в окне
for i in range(len(all_tokens) - window_size + 1):
    window = all_tokens[i:i + window_size]
    for j in range(len(window)):
        for k in range(j + 1, len(window)):
            word_j = window[j]
            word_k = window[k]
            if word_j in word_to_index and word_k in word_to_index:
                idx_j = word_to_index[word_j]
                idx_k = word_to_index[word_k]
                co_occurrence_matrix[idx_j][idx_k] += 1
                co_occurrence_matrix[idx_k][idx_j] += 1  # Симметричная матрица

# Нормализуем матрицу, чтобы значения были в диапазоне от 0 до 1
co_occurrence_matrix = co_occurrence_matrix / np.max(co_occurrence_matrix)

# Преобразование в DataFrame для удобного отображения
co_occurrence_df = pd.DataFrame(co_occurrence_matrix, index=vocab, columns=vocab)

# Визуализация - Тепловая карта совместной частоты
plt.figure(figsize=(12, 10))
sns.heatmap(co_occurrence_df, annot=False, cmap='YlGnBu', xticklabels=10, yticklabels=10)
plt.title("Тепловая карта совместной частоты слов")
plt.xlabel("Слова")
plt.ylabel("Слова")
plt.savefig("co_occurrence_heatmap.png")  # Сохранение изображения
plt.close()  # Закрытие текущей фигуры

# Рассчитываем косинусное сходство между словами
cosine_sim = cosine_similarity(co_occurrence_matrix)

# Преобразуем матрицу сходства в DataFrame
cosine_sim_df = pd.DataFrame(cosine_sim, index=vocab, columns=vocab)

# Визуализация - Тепловая карта косинусного сходства
plt.figure(figsize=(12, 10))
sns.heatmap(cosine_sim_df, annot=False, cmap='YlGnBu', xticklabels=10, yticklabels=10)
plt.title("Тепловая карта косинусного сходства слов")
plt.xlabel("Слова")
plt.ylabel("Слова")
plt.savefig("cosine_similarity_heatmap.png")  # Сохранение изображения
plt.close()  # Закрытие текущей фигуры

# Визуализация - Облако слов для самых частых слов
wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
plt.figure(figsize=(10, 6))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("Облако слов для сид-фраз")
plt.savefig("wordcloud.png")  # Сохранение изображения
plt.close()  # Закрытие текущей фигуры
