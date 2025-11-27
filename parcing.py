import asyncio
import json
import os
import re
from pyrogram import Client
from pyrogram.enums import MessageMediaType

# --- КОНФИГУРАЦИЯ ---
# Используем os.environ.get для работы и локально, и на GitHub Actions
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
    
    # Условие 1: "ціна:" И "#наявність"
    cond1 = "ціна:" in text_lower and "#наявність" in text_lower
    # Условие 2: "#передзамовлення"
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
    elif message.document: return "." + (message.document.mime_type.split('/')[-1] if message.document.mime_type else "bin")
    elif message.video: return "." + (message.video.mime_type.split('/')[-1] if message.video.mime_type else "bin")
    elif message.sticker: return ".webp"
    return ".bin"


# --- ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА ---
async def parse_channel():
    print("-> Запуск парсинга канала...")
    
    # Настройка клиента
    app = Client(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await app.start()
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return 
    
    dolls_data = []
    processed_count = 0 
    
    # Увеличим лимит, чтобы захватить больше постов
    async for message in app.get_chat_history(CHANNEL_USERNAME, limit=100): 
        processed_count += 1
        
        # 1. Получаем текст
        post_content = message.text or message.caption or ""
        
        # 2. Проверяем фильтр (ДЛЯ ОТЛАДКИ)
        is_filtered = filter_post(post_content)
        
        # 3. Визуальный вывод (Вернул по твоей просьбе)
        # Обрезаем текст для консоли, чтобы не был слишком длинным
        clean_text_preview = post_content.replace('\n', ' ').strip()
        short_text = (clean_text_preview[:40] + '...') if len(clean_text_preview) > 40 else (clean_text_preview or "--- НЕТ ТЕКСТА ---")
        
        print(f"[{processed_count}] ID:{message.id} | ФИЛЬТР: {'✅' if is_filtered else '❌'} | ТЕКСТ: {short_text}")

        # 4. Если пост прошел фильтр — обрабатываем
        if post_content and is_filtered:
            prices = extract_prices(post_content)
            
            # === ИСПРАВЛЕНИЕ ОШИБКИ COMMENT COUNT ===
            # Безопасно проверяем наличие атрибута replies через getattr
            comments_count = 0
            replies_obj = getattr(message, "replies", None)
            if replies_obj:
                comments_count = getattr(replies_obj, "replies", 0)
            # =========================================
            
            doll_entry = {
                "id": message.id,
                "text": post_content, 
                "photo_path": None,
                "photo_count": 1, 
                "comment_count": comments_count, 
                "is_preorder": "#передзамовлення" in post_content.lower(),
                "link": f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}/{message.id}",
                "price": prices["price"],
                "delivery_price": prices["delivery_price"]
            }
            
            media_to_download = None
            
            # === ЛОГИКА АЛЬБОМОВ ===
            # Скачиваем только если это первая часть альбома или одиночное фото
            should_download = False
            
            if message.media_group_id:
                try:
                    media_files = await app.get_media_group(message.chat.id, message.id)
                    if media_files and message.id == media_files[0].id:
                        media_to_download = media_files[0]
                        doll_entry["photo_count"] = len(media_files)
                        should_download = True
                except Exception:
                    pass
            elif message.photo or message.document:
                media_to_download = message
                should_download = True

            # Скачивание файла
            if should_download and media_to_download:
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
                    print(f"  ⚠️ Ошибка скачивания фото {message.id}: {e}")

            # Добавляем в список
            dolls_data.append(doll_entry)
            print(f"  [+] Добавлено в базу: {doll_entry['price']} грн, Комментов: {doll_entry['comment_count']}") 
            
    await app.stop()
    
    # Сохранение JSON
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(dolls_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n-> ✅ Парсинг завершен. Сохранено {len(dolls_data)} товаров в {OUTPUT_JSON_FILE}")

if __name__ == "__main__":
    asyncio.run(parse_channel())
