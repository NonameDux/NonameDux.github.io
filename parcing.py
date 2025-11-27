import asyncio
import json
import os
import re
import glob
from pyrogram import Client
from pyrogram.errors import FloodWait

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0)) 
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
CHANNEL_USERNAME = "@kabi_mlp"
OUTPUT_JSON_FILE = "static/dolls_data.json" 
MEDIA_DIR = "static/doll_images" 
SESSION_NAME = "dolls_parser_session"

os.makedirs("static", exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# --- ФУНКЦИЯ ЗАДЕРЖКИ (FLOOD WAIT) ---
async def safe_execution(coro):
    while True:
        try:
            return await coro
        except FloodWait as e:
            wait_time = e.value + 5
            print(f"⚠️ [FLOOD] Ждем {wait_time} с...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            raise e

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def filter_post(text: str) -> bool:
    if not text: return False
    text_lower = text.lower()
    cond1 = "ціна:" in text_lower and "#наявність" in text_lower
    cond2 = "#передзамовлення" in text_lower 
    return cond1 or cond2

def extract_prices(text: str) -> dict:
    data = {"price": None, "delivery_price": None}
    text_lower = text.lower()
    price_match = re.search(r"ціна:.*?(\d+)", text_lower)
    if price_match:
        data["price"] = price_match.group(1) 
        start_pos = price_match.end(0)
        delivery_match = re.search(r"\+\s*(\d+)\s*дс", text_lower[start_pos:start_pos + 50])
        if delivery_match:
            data["delivery_price"] = delivery_match.group(1)
    return data

def get_file_extension(message) -> str:
    if message.photo: return ".jpg"
    elif message.document: return "." + (message.document.mime_type.split('/')[-1] if message.document.mime_type else "bin")
    elif message.video: return "." + (message.video.mime_type.split('/')[-1] if message.video.mime_type else "bin")
    return ".bin"

def find_existing_photo(message_id: int):
    pattern = os.path.join(MEDIA_DIR, f"{message_id}_photo.*")
    found_files = glob.glob(pattern)
    if found_files:
        full_path = found_files[0].replace(os.sep, '/')
        if "static/" in full_path:
            return full_path[full_path.find("static/"):]
        return full_path
    return None

# --- ОСНОВНАЯ ФУНКЦИЯ ---
async def parse_channel():
    print("-> 🚀 Запуск исправленного парсера...")
    
    app = Client(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await safe_execution(app.start())
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return 
    
    dolls_data = []
    
    # Чтобы не обрабатывать дубликаты из одной медиа-группы
    processed_media_groups = set()

    try:
        async for message in app.get_chat_history(CHANNEL_USERNAME, limit=500): 
            # Пропускаем, если это часть альбома, который мы уже обработали (чтобы не было дублей товаров)
            if message.media_group_id and message.media_group_id in processed_media_groups:
                continue

            post_content = message.text or message.caption or ""
            
            if post_content and filter_post(post_content):
                prices = extract_prices(post_content)
                
                # 1. СЧИТАЕМ КОММЕНТАРИИ
                comments_count = 0
                try:
                    if message.replies:
                        comments_count = message.replies.replies
                except:
                    pass

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
                
                # 2. ОПРЕДЕЛЯЕМ ФОТО (ГРУППА ИЛИ ОДИНОЧНОЕ)
                media_to_download = None
                
                if message.media_group_id:
                    processed_media_groups.add(message.media_group_id)
                    try:
                        # Получаем все фото альбома, чтобы узнать их количество
                        media_group = await safe_execution(app.get_media_group(message.chat.id, message.id))
                        doll_entry["photo_count"] = len(media_group)
                        media_to_download = media_group[0] # Берем первое фото
                    except Exception as e:
                        print(f"Ошибка получения альбома {message.id}: {e}")
                        media_to_download = message
                else:
                    media_to_download = message

                # 3. ПРОВЕРЯЕМ ФАЙЛ ИЛИ КАЧАЕМ
                existing_photo = find_existing_photo(message.id)
                
                if existing_photo:
                    doll_entry["photo_path"] = existing_photo
                    print(f"  [Skip] {message.id} (Фото есть, {doll_entry['photo_count']} шт в альбоме)")
                elif media_to_download:
                    try:
                        ext = get_file_extension(media_to_download)
                        file_name = os.path.join(MEDIA_DIR, f"{message.id}_photo{ext}")
                        
                        file_path = await safe_execution(
                            app.download_media(media_to_download, file_name=file_name)
                        )
                        
                        web_path = file_path.replace(os.sep, '/')
                        if "static/" in web_path:
                            doll_entry["photo_path"] = web_path[web_path.find("static/"):]
                        else:
                            doll_entry["photo_path"] = web_path
                        print(f"  [Down] {message.id} (Скачано)")
                    except Exception as e:
                        print(f"  ⚠️ Не удалось скачать фото {message.id}: {e}")

                dolls_data.append(doll_entry)
                
    except FloodWait as e:
        print(f"CRITICAL FLOOD WAIT: {e.value}")
        await asyncio.sleep(e.value + 10)
    except Exception as e:
        print(f"Global Error: {e}")

    await app.stop()
    
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(dolls_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n-> ✅ Готово! Товаров: {len(dolls_data)}")

if __name__ == "__main__":
    asyncio.run(parse_channel())

