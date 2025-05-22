import requests
import praw
import re
import time
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Устанавливаем базовый уровень логирования
logging.basicConfig(level=logging.INFO)

# URL словаря BIP-39 на GitHub
url = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"

# Функция для получения и загрузки словаря BIP-39
def download_bip39_words(url):
    try:
        # Отправляем запрос на получение данных
        response = requests.get(url)

        # Проверяем успешность запроса
        if response.status_code == 200:
            # Разделяем слова по строкам
            bip39_words = response.text.strip().split("\n")
            
            # Проверяем, что список не пуст
            if not bip39_words:
                logging.warning("Словарь пустой!")
                return []
            
            logging.info(f"Загружено {len(bip39_words)} слов из BIP-39.")
            return bip39_words
        else:
            logging.error(f"Ошибка при загрузке словаря: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        # Обработка ошибок запросов (например, ошибки сети)
        logging.error(f"Ошибка сети: {e}")
        return []

# Загрузка словаря BIP-39
bip39_words = download_bip39_words(url)

# Если словарь загружен, например, сохраняем его в файл
if bip39_words:
    with open("bip39_words.txt", "w") as file:
        for word in bip39_words:
            file.write(f"{word}\n")
    logging.info("Словарь BIP-39 сохранен в файл bip39_words.txt.")

# Настройка Reddit API через praw
reddit = praw.Reddit(
    client_id=os.getenv('client_id'),  # Ваш client_id
    client_secret=os.getenv('client_secret'),  # Ваш client_secret
    user_agent="SeedPhraseParser u/SuspiciousUse22",  # Ваш user_agent
)

# --------------- ЗАГРУЗКА СЛОВАРЯ BIP-39 ----------------
def load_bip39_wordlist(path="bip39_words.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(word.strip() for word in f if word.strip())
    except FileNotFoundError:
        print(f"❌ Файл {path} не найден. Поместите BIP-39 словарь рядом со скриптом.")
        exit(1)

# --------------- ИЗВЛЕЧЕНИЕ ФРАЗ И СЛОВ ----------------
def extract_seed_elements(text, bip39_words):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    valid_words = [w for w in words if w in bip39_words]

    unique_phrases = set()
    single_words = set(valid_words)  # сохраняем все уникальные слова

    def extract_chunks(size):
        for i in range(len(valid_words) - size + 1):
            chunk = valid_words[i:i+size]
            phrase = " ".join(chunk)
            unique_phrases.add(phrase)

    extract_chunks(12)
    extract_chunks(24)

    return unique_phrases, single_words

# --------------- ФИЛЬТР ПО ДАТЕ ----------------
def is_post_in_date_range(post_date, start_date, end_date):
    return start_date <= post_date <= end_date

# --------------- ПАРСИНГ ОДНОГО САБРЕДДИТА ----------------
def parse_subreddit(subreddit_name, start_date, end_date, bip39_words, time_filter="all"):
    print(f"🔍 Парсим: r/{subreddit_name}")
    phrases = set()
    singles = set()
    try:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.top(limit=100000, time_filter=time_filter):
            post_date = datetime.utcfromtimestamp(submission.created_utc)
            if is_post_in_date_range(post_date, start_date, end_date):
                p1, s1 = extract_seed_elements(submission.title, bip39_words)
                p2, s2 = extract_seed_elements(submission.selftext, bip39_words)
                phrases.update(p1)
                phrases.update(p2)
                singles.update(s1)
                singles.update(s2)
    except Exception as e:
        print(f"⚠️ Ошибка в r/{subreddit_name}: {e}")
    return phrases, singles

# --------------- ПАРСИНГ НЕСКОЛЬКИХ САБРЕДДИТОВ ----------------
def parse_multiple_subreddits(subreddits, start_date, end_date, bip39_words, time_filter="all"):
    all_phrases = set()
    all_single_words = set()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(parse_subreddit, sub, start_date, end_date, bip39_words, time_filter): sub
            for sub in subreddits
        }
        for future in as_completed(futures):
            phrases, singles = future.result()
            all_phrases.update(phrases)
            all_single_words.update(singles)
    return all_phrases, all_single_words

# --------------- СОХРАНЕНИЕ ----------------
def save_to_file(items, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for item in sorted(items):
                f.write(item + "\n")
        print(f"✅ Сохранено {len(items)} уникальных записей в {filename}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении {filename}: {e}")

# --------------- ДАТА ----------------
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

# --------------- ГЛАВНЫЙ ЗАПУСК ----------------
if __name__ == "__main__":
    bip39_words = load_bip39_wordlist("bip39_words.txt")

    # Период анализа
    start_date = parse_date("2023-01-01")
    end_date = parse_date("2025-05-20")

    # Список сабреддитов
    subreddits = [
        "CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets",
        "seedstorage", "CryptoTechnology", "dogecoin", "solana",
        "blockchain", "Stellar", "btc"
    ]

    # Парсим Reddit
    full_phrases, single_words = parse_multiple_subreddits(
        subreddits, start_date, end_date, bip39_words, time_filter="all"
    )

    # Сохраняем
    save_to_file(full_phrases, "only_full_phrases.txt")
    save_to_file(single_words, "single_bip39_words.txt")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ваш GitHub токен
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Базовый URL GitHub API
API_BASE = "https://api.github.com"

# Регулярное выражение для поиска seed-фраз
SEED_REGEX = re.compile(r"\b(?:[a-z]{3,}\s){11,23}[a-z]{3,}\b", re.IGNORECASE)

# Загрузка словаря BIP-39
def load_bip39_wordlist():
    url = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
    response = requests.get(url)
    if response.status_code == 200:
        return set(response.text.strip().split("\n"))
    else:
        logging.error("Не удалось загрузить BIP-39 словарь")
        return set()

# Фильтрация seed-фраз из текста
def extract_seed_phrases(text, bip39_words):
    phrases = []
    for match in SEED_REGEX.findall(text):
        words = match.lower().split()
        if all(word in bip39_words for word in words):
            phrases.append(" ".join(words))
    return phrases

# Получение списка репозиториев с темой bip39
def get_repositories_with_topic(topic, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    page = 1
    while True:
        url = f"{API_BASE}/search/repositories?q=topic:{topic}&page={page}&per_page=100"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Ошибка при получении репозиториев: {response.status_code}")
            break
        data = response.json()
        if not data['items']:
            break
        repos.extend(data['items'])
        page += 1
    return repos

# Получение содержимого файлов репозитория
def fetch_seed_phrases_from_repo(owner, repo, bip39_words, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    seeds = []
    contents_url = f"{API_BASE}/repos/{owner}/{repo}/contents"
    try:
        response = requests.get(contents_url, headers=headers)
        if response.status_code != 200:
            logging.warning(f"Ошибка доступа к {owner}/{repo}: {response.status_code}")
            return []

        files = response.json()
        for file in files:
            if file["type"] == "file" and file["name"].endswith((".txt", ".md", ".py", ".js")):
                file_resp = requests.get(file["download_url"])
                if file_resp.status_code == 200:
                    seeds += extract_seed_phrases(file_resp.text, bip39_words)
                time.sleep(1)  # Задержка для обхода лимита
    except Exception as e:
        logging.error(f"Ошибка при обработке {owner}/{repo}: {e}")
    return seeds

# Основной запуск
if __name__ == "__main__":
    bip39_words = load_bip39_wordlist()
    all_seeds = []

    repos = get_repositories_with_topic("bip39", GITHUB_TOKEN)
    logging.info(f"Найдено {len(repos)} репозиториев с темой 'bip39'.")

    for repo in repos:
        owner = repo['owner']['login']
        name = repo['name']
        logging.info(f"Обработка {owner}/{name}...")
        seeds = fetch_seed_phrases_from_repo(owner, name, bip39_words, GITHUB_TOKEN)
        all_seeds.extend(seeds)

    if all_seeds:
        with open("seed_phrases_from_github.txt", "w", encoding="utf-8") as f:
            for phrase in all_seeds:
                f.write(phrase + "\n")
        logging.info(f"Найдено и сохранено {len(all_seeds)} seed-фраз.")
    else:
        logging.warning("Seed-фразы не найдены.")