import asyncio
import json
import os
import re
from pyrogram import Client
from pyrogram.enums import MessageMediaType

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0)) 
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
CHANNEL_USERNAME = "@kabi_mlp"
OUTPUT_JSON_FILE = "static/dolls_data.json" 
MEDIA_DIR = "static/doll_images" 
SESSION_NAME = "dolls_parser_session"

# Создаем папки
os.makedirs("static", exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)


# --- ФУНКЦИЯ ФИЛЬТРАЦИИ ---
def filter_post(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    
    cond1 = "ціна:" in text_lower and "#наявність" in text_lower
    cond2 = "#передзамовлення" in text_lower 
    return cond1 or cond2


# --- ИЗВЛЕЧЕНИЕ ЦЕН ---
def extract_prices(text: str) -> dict:
    data = {"price": None, "delivery_price": None}
    text_lower = text.lower()
    
    # Ищем цену (первое число после "ціна:")
    price_match = re.search(r"ціна:.*?(\d+)", text_lower)
    if price_match:
        data["price"] = price_match.group(1) 
        
        # Ищем доставку (+ число дс)
        start_pos = price_match.end(0)
        delivery_match = re.search(r"\+\s*(\d+)\s*дс", text_lower[start_pos:start_pos + 50])
        if delivery_match:
            data["delivery_price"] = delivery_match.group(1)
            
    return data


# --- ПОЛУЧЕНИЕ РАСШИРЕНИЯ ---
def get_file_extension(message) -> str:
    if message.photo: return ".jpg"
    elif message.document: mime = message.document.mime_type
    elif message.video: mime = message.video.mime_type
    elif message.sticker: return ".webp"
    else: return ".bin"
    
    if mime: return "." + mime.split('/')[-1]
    return ".bin"


# --- ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА ---
async def parse_channel():
    print("-> Запуск парсинга канала...")
    app = Client(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await app.start()
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return 
    
    dolls_data = []
    processed_count = 0 
    
    # Увеличим лимит для лучшего поиска
    async for message in app.get_chat_history(CHANNEL_USERNAME, limit=100): 
        processed_count += 1
        
        post_content = message.text or message.caption or ""
        
        # Отладка
        short_text = (post_content[:30] + '...') if len(post_content) > 30 else post_content
        print(f"[{processed_count}] ID:{message.id} | Текст: {short_text}")

        if post_content and filter_post(post_content):
            prices = extract_prices(post_content)
            
            # === НОВОЕ: Получаем кол-во комментариев ===
            # message.replies содержит информацию о комментариях
            comments = message.replies if message.replies else 0
            
            doll_entry = {
                "id": message.id,
                "text": post_content, 
                "photo_path": None,
                "photo_count": 1, # По умолчанию 1 фото
                "comment_count": comments, # Сохраняем кол-во комментов
                "is_preorder": "#передзамовлення" in post_content.lower(),
                "link": f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}/{message.id}",
                "price": prices["price"],
                "delivery_price": prices["delivery_price"]
            }
            
            media_to_download = None
            is_album = False
            
            # === ЛОГИКА АЛЬБОМОВ (НЕСКОЛЬКО ФОТО) ===
            if message.media_group_id:
                try:
                    media_files = await app.get_media_group(message.chat.id, message.id)
                    # Проверяем, что это главное сообщение группы
                    if media_files and message.id == media_files[0].id:
                        media_to_download = media_files[0]
                        is_album = True
                        doll_entry["photo_count"] = len(media_files) # Пишем реальное кол-во фото
                    else:
                        # Если это не первое сообщение альбома, пропускаем скачивание,
                        # но запись о кукле уже создана выше? Нет, нам нужно избегать дублей.
                        # В текущей логике фильтр по тексту отсеет дубли, т.к. текст только у первого.
                        pass
                except Exception:
                    pass
            
            # Логика для одиночных фото
            elif message.photo:
                media_to_download = message
            elif message.media == MessageMediaType.DOCUMENT:
                 media_to_download = message

            # Скачивание
            if media_to_download:
                try:
                    ext = get_file_extension(media_to_download)
                    file_name = os.path.join(MEDIA_DIR, f"{message.id}_photo{ext}")
                    
                    file_path = await app.download_media(media_to_download, file_name=file_name)
                    
                    # Путь для веба
                    web_path = file_path.replace(os.sep, '/')
                    if "static/" in web_path:
                        doll_entry["photo_path"] = web_path[web_path.find("static/"):]
                    else:
                        doll_entry["photo_path"] = web_path
                        
                except Exception as e:
                    print(f"Ошибка фото {message.id}: {e}")

            # Добавляем только если есть фото (или если фото не обязательно - уберите проверку)
            if doll_entry["photo_path"]:
                dolls_data.append(doll_entry)
                print(f"  [+] Добавлено ID: {message.id} (Фото: {doll_entry['photo_count']}, Комм: {doll_entry['comment_count']})") 
            
    await app.stop()
    
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(dolls_data, f, ensure_ascii=False, indent=4)
        
    print(f"-> Готово. Сохранено {len(dolls_data)} товаров.")

if __name__ == "__main__":
    asyncio.run(parse_channel())

