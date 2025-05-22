def load_bip39_wordlist(path="bip39_words.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(word.strip() for word in f if word.strip())
    except FileNotFoundError:
        print(f"❌ Файл {path} не найден. Поместите словарь BIP-39 рядом со скриптом.")
        exit(1)


def clean_valid_unique_seed_phrases(input_file="only_full_phrases.txt",
                                     output_file="cleaned_seed_phrases_from_reddit.txt"):
    bip39_words = load_bip39_wordlist()

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            raw_phrases = [line.strip() for line in f if line.strip()]

        total_before = len(raw_phrases)
        valid_phrases = []

        for phrase in raw_phrases:
            words = phrase.strip().lower().split()
            word_count = len(words)

            # Условие: длина 12 или 24, все слова уникальны, и все из BIP-39
            if word_count in (12, 24) and len(set(words)) == word_count and all(word in bip39_words for word in words):
                valid_phrases.append(" ".join(words))

        unique_valid_phrases = sorted(set(valid_phrases))
        total_after = len(unique_valid_phrases)

        with open(output_file, "w", encoding="utf-8") as f:
            for phrase in unique_valid_phrases:
                f.write(phrase + "\n")

        print("✅ Очистка завершена.")
        print(f"📄 Всего фраз: {total_before}")
        print(f"✔️ Подходящих (12/24 слов, все уникальны, из BIP-39): {len(valid_phrases)}")
        print(f"✅ Уникальных: {total_after}")
        print(f"💾 Сохранено в файл: {output_file}")

    except FileNotFoundError:
        print(f"❌ Файл {input_file} не найден.")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")


# ---------------- Запуск ----------------
if __name__ == "__main__":
    clean_valid_unique_seed_phrases()