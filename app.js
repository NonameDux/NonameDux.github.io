// Функция для переключения вкладок
function openTab(evt, tabName) {
    // Объявляем переменные
    let i, tabcontent, tablinks;

    // Скрываем весь контент вкладок
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.add("hidden");
        tabcontent[i].setAttribute('aria-selected', 'false');
    }

    // Убираем класс 'active' со всех кнопок вкладок
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        // Удаляем только класс 'active'
        tablinks[i].classList.remove("active");
        tablinks[i].setAttribute('aria-selected', 'false');
    }

    // Показываем текущую вкладку и добавляем класс 'active' к кнопке
    document.getElementById(tabName).classList.remove("hidden");
    document.getElementById(tabName).setAttribute('aria-selected', 'true');
    
    // Применяем активные стили к нажатой кнопке
    // Добавляем только класс 'active'
    evt.currentTarget.classList.add("active");
    evt.currentTarget.setAttribute('aria-selected', 'true');
}

// Автоматическая активация первой вкладки при загрузке
window.onload = function() {
    // Имитация клика по первой вкладке для установки стилей
    const firstTab = document.querySelector('.tab-btn');
    if (firstTab) {
        // Вызываем openTab с данными первой вкладки
        openTab({ currentTarget: firstTab }, firstTab.getAttribute('data-tab-name'));
    }
};

/**
 * Асинхронная функция для определения ориентации изображения по его URL.
 * @param {string} url - URL изображения.
 * @returns {Promise<string>} 'portrait' или 'landscape'.
 */
function checkImageOrientation(url) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = function() {
            console.log(`[Orientation Check] Loaded image: W=${this.width}, H=${this.height}`); // LOG: Размеры загруженного изображения
            // Сравниваем ширину и высоту
            if (this.width > this.height) {
                console.log('[Orientation Check] Result: landscape'); // LOG
                resolve('landscape');
            } else if (this.height > this.width) {
                console.log('[Orientation Check] Result: portrait'); // LOG
                resolve('portrait');
            } else {
                // Квадратное изображение
                console.log('[Orientation Check] Result: square'); // LOG
                resolve('square');
            }
        };
        img.onerror = function() {
            console.error(`[Orientation Check] Error loading image from URL: ${url}`); // LOG: Ошибка загрузки
            // В случае ошибки загрузки, по умолчанию считаем горизонтальным
            resolve('landscape'); 
        };
        img.src = url;
    });
}

/**
 * Открывает модальное окно с указанным изображением и описанием.
 * @param {string} imgSrc - URL изображения.
 * @param {string} imgDesc - Текстовое описание изображения.
 */
async function openImageModal(imgSrc, imgHead, imgDesc) {
    const modal = document.getElementById('image-modal');
    const content = document.querySelector('.modal-content');
    const image = document.getElementById('modal-image');
    const description = document.getElementById('modal-description');
    const heading = document.getElementById('modal-heading');
    
    // 1. Сбрасываем старые классы ориентации
    image.classList.remove('portrait', 'landscape', 'square');
    console.log('[Modal Open] Cleared old orientation classes.'); // LOG

    // 2. Заполняем содержимое модального окна
    image.src = imgSrc;
    image.alt = imgDesc;
    description.textContent = imgDesc;
    heading.textContent = imgHead;

    // 3. Асинхронно проверяем ориентацию
    const orientation = await checkImageOrientation(imgSrc);
    
    // 4. Добавляем соответствующий класс для стилизации
    image.classList.add(orientation);
    console.log(`[Modal Open] Added new class: ${orientation}`); // LOG

    // 5. Показываем модальное окно, удаляя класс 'hidden'
    modal.classList.remove('hidden');
}

/**
 * Скрывает модальное окно.
 */
function closeModal() {
    const modal = document.getElementById('image-modal');
    const content = document.querySelector('.modal-content');
    
    // 1. Скрываем модальное окно, добавляя класс 'hidden'
    modal.classList.add('hidden');
    
    // 2. Очищаем содержимое и классы
    document.getElementById('modal-image').src = '';
    document.getElementById('modal-description').textContent = '';
    document.getElementById('modal-heading').textContent = '';
    content.classList.remove('portrait', 'landscape', 'square'); // Очистка классов при закрытии
    console.log('[Modal Close] Modal closed and orientation classes cleared.'); // LOG
}

// Обработчик для клавиши ESCAPE (Esc)
document.addEventListener('keydown', function(event) {
    const modal = document.getElementById('image-modal');
    // Если нажата Escape и модальное окно видимо (не имеет класса 'hidden')
    if (event.key === 'Escape' && !modal.classList.contains('hidden')) {
        closeModal();
    }
});

// Гарантируем, что модальное окно скрыто при загрузке страницы
window.onload = function() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
};
//=================================PLAYER===================
 // ДАННЫЕ ПЛЕЙЛИСТА
const playlist = [
    // ЗАМЕНИТЕ ЭТИ ССЫЛКИ НА ВАШИ ФАЙЛЫ
    { title: "Монеточка - Это было в Росии", description: "Как мне кажется твоя любимая песня, про неё и о ней ты рассказывала больше всего.", src: "music/vrosii.mp3" },
    { title: "Нервы - Счастье", description: "Песенка с которой ты мне сделала открытка, я очень её ценю и люблю, как и тебя, я рад что у меня есть такое Счастье как ты :3", src: "music/Shastie.mp3"},
    { title: "ПМ - Ты разбила папину машину", description: "Ты ПМ тоже любишь но из-за одного из тик токов вспомнилась именно эта песня, тоже люблю пм, но тебя больше!", src: "music/Papinu_machinu.mp3"},
    { title: "Нойз,Монеточка - Люди с автоматами", description: "Я люблю когда ты поёшь, но в особенности люблю когда ты поёшь монеточку, хоть тут и нойз тоже но эту песню в твоём исполнении я очень люблю!", src: "music/Ludi_s_avtomatami.mp3"},
    { title: "Оля Ля -Солнцем", description: "Когда первый раз услышал хотел что-бы эта песня была про нас, не юудем учитывать грустный контекст, просто мне нравится как она радовалась что её зовут солнцем, я так же радуюсь вхвххв :3", src: "music/Solnce.mp3"},
    { title: "Нервы - Подоконник", description: "Как ты мне только что сказала твоя одна из любимых песен нервов, и ты нас с ней ассоциируешь чучут не учитывая грустное, ты вроде её на стриме у мильковского ещё просила хвхв", src: "music/Podokonnik.mp3"},
    { title: "Нойз - Детка, послушай", description: "А эта песня мне попалась пока я искал другие но она тоже довольно часто играла у нас, мне нравится", src: "music/detkaposlushai.mp3"},

];
let currentSongIndex = -1; // Индекс текущей песни

// ССЫЛКИ НА DOM-ЭЛЕМЕНТЫ
const audio = document.getElementById('audio-element');
const playPauseBtn = document.getElementById('play-pause-btn');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const currentTimeEl = document.getElementById('current-time');
const durationEl = document.getElementById('duration');
const songTitleEl = document.getElementById('song-title');
const songDescEl = document.getElementById('song-description');
const playlistListEl = document.getElementById('playlist-list');


// Вспомогательная функция для форматирования времени (секунды -> MM:SS)
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    const paddedSeconds = remainingSeconds < 10 ? '0' + remainingSeconds : remainingSeconds;
    return `${minutes}:${paddedSeconds}`;
}

/**
 * Загружает и воспроизводит песню из плейлиста.
 * @param {number} index - Индекс песни в массиве playlist.
 * @param {boolean} [autoPlay=true] - Начинать ли воспроизведение сразу.
 */
function loadSong(index, autoPlay = true) {
    // Если индекс вне диапазона, возвращаемся к первой песне
    if (index < 0 || index >= playlist.length) {
        index = 0;
    }

    // Если клик по той же песне, просто продолжаем
    if (index === currentSongIndex && !audio.paused && autoPlay) {
        return; 
    }
    
    currentSongIndex = index;
    const song = playlist[index];
    
    // 1. Обновляем плеер
    audio.src = song.src;
    songTitleEl.textContent = song.title;
    songDescEl.textContent = song.description;
    
    // 2. Сброс прогресса
    progressBar.style.width = '0%';
    currentTimeEl.textContent = '0:00';
    durationEl.textContent = '0:00';
    
    // 3. Загружаем и обновляем кнопку
    audio.load();
    audio.oncanplay = () => {
        // После загрузки метаданных, обновляем общую длительность
        durationEl.textContent = formatTime(audio.duration);
        if (autoPlay) {
            audio.play();
            playPauseBtn.textContent = '⏸';
        } else {
            playPauseBtn.textContent = '▶';
        }
    };
    
    // 4. Обновляем активный класс в плейлисте
    document.querySelectorAll('.playlist-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });
}


// --- 1. УПРАВЛЕНИЕ ВОСПРОИЗВЕДЕНИЕМ ---
playPauseBtn.addEventListener('click', () => {
    if (currentSongIndex === -1 && playlist.length > 0) {
        // Если плеер пуст, загружаем первую песню
        loadSong(0, true);
        return;
    }
    
    if (audio.paused) {
        audio.play();
        playPauseBtn.textContent = '⏸'; 
    } else {
        audio.pause();
        playPauseBtn.textContent = '▶'; 
    }
});

// --- 2. ОБНОВЛЕНИЕ ПРОГРЕССА ---
audio.addEventListener('timeupdate', () => {
    if (isNaN(audio.duration) || audio.duration === 0) return;
    
    // Рассчитываем процент проигрывания
    const progressPercent = (audio.currentTime / audio.duration) * 100;
    progressBar.style.width = `${progressPercent}%`;
    
    // Обновляем текущее время
    currentTimeEl.textContent = formatTime(audio.currentTime);
});

// --- 3. ПЕРЕМОТКА ПО КЛИКУ НА ПОЛОСЕ ---
progressContainer.addEventListener('click', (e) => {
    if (isNaN(audio.duration) || audio.duration === 0) return;
    
    const width = progressContainer.clientWidth;
    const clickX = e.offsetX;
    const newTime = (clickX / width) * audio.duration;
    
    audio.currentTime = newTime;
});

// --- 4. АВТОПЕРЕКЛЮЧЕНИЕ ПЕСЕН ---
audio.addEventListener('ended', () => {
    const nextIndex = (currentSongIndex + 1) % playlist.length;
    loadSong(nextIndex);
});

// --- 5. СОЗДАНИЕ ПЛЕЙЛИСТА И ПЕРВОНАЧАЛЬНАЯ ЗАГРУЗКА ---
function renderPlaylist() {
    playlistListEl.innerHTML = ''; 
    playlist.forEach((song, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'playlist-item';
        listItem.textContent = song.title;
        // При клике загружаем эту песню
        listItem.onclick = () => loadSong(index); 
        playlistListEl.appendChild(listItem);
    });
    
    // Загружаем первую песню при старте, но не включаем автоплей
    if (playlist.length > 0) {
        loadSong(0, false);
    }
}


//========================================LOVE LETTERS=========================
/**
         * Переключает состояние Аккордеона (открыть/закрыть).
         * @param {HTMLElement} header - Элемент заголовка, по которому был клик.
         */   
        function toggleAccordion(header) {
            // Находим следующий элемент — блок с содержимым
            const content = header.nextElementSibling;
            
            // Переключаем класс 'active' для заголовка (для изменения стилей, например, стрелки)
            header.classList.toggle('active');

            // Переключаем класс 'show' для содержимого
            content.classList.toggle('show');
            
            // ВАЖНО: Управление высотой для анимации
            // Если блок открыт (имеет класс 'show'):
            if (content.classList.contains('show')) {
                // Устанавливаем max-height равным фактической высоте контента
                // Это нужно, чтобы анимация была точной, а не просто до 500px.
                // ScrollHeight - это реальная высота контента, даже если он скрыт.
                content.style.maxHeight = content.scrollHeight + "px";
            } else {
                // Если блок закрыт, устанавливаем max-height обратно в 0
                content.style.maxHeight = "0";
            }
        }
        
        // Опционально: Принудительное закрытие всех аккордеонов при загрузке
        window.onload = function() {
            document.querySelectorAll('.accordion-content').forEach(content => {
                content.style.maxHeight = "0";
                content.classList.remove('show');
            });
            document.querySelectorAll('.accordion-header').forEach(header => {
                header.classList.remove('active');
            });
        };
window.onload = renderPlaylist;