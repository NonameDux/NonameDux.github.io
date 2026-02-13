    // --- ЛОГИКА ВОПРОСА ---

        function runAway(btn) {
            // Кнопка плавно убегает
            btn.style.position = 'fixed'; // Фиксируем, чтобы летала по всему экрану
            const x = Math.random() * (window.innerWidth - btn.offsetWidth - 50);
            const y = Math.random() * (window.innerHeight - btn.offsetHeight - 50);
            
            btn.style.left = x + 'px';
            btn.style.top = y + 'px';
        }

        function unlockSite() {
            const screenQuestion = document.getElementById('screen-question');
            const mainContent = document.getElementById('main-content');
            
            // 1. Убираем вопрос
            screenQuestion.style.opacity = '0';
            screenQuestion.style.transform = 'scale(1.5)'; // Эффект приближения при исчезновении
            
            setTimeout(() => {
                screenQuestion.style.display = 'none';
                
                // 2. Включаем скролл и показываем контент
                document.body.style.height = 'auto'; // Разрешаем растягиваться
                document.body.style.overflow = 'auto'; // Включаем скроллбар
                
                mainContent.style.display = 'block';
                // Небольшая задержка чтобы браузер понял что display изменился
                setTimeout(() => {
                    mainContent.style.opacity = '1';
                }, 50);
                
            }, 800);
        }

        // --- ЛОГИКА ЗВЕЗД (ПАРАЛЛАКС) ---
        // Тот самый код, который работал
        document.addEventListener("DOMContentLoaded", () => {
            const container = document.getElementById('star-container');
            const count = 120; 
            const stars = [];

            // Создаем звезды
            for (let i = 0; i < count; i++) {
                const s = document.createElement('div');
                s.className = 'star';
                const x = Math.random() * 100;
                const y = Math.random() * 100;
                const isStatic = Math.random() < 0.1; 
                const speed = isStatic ? 0 : 0.05 + Math.random() * 0.1; 
                const size = Math.random() * 2 + 1;
                const duration = Math.random() * 3 + 2;

                s.style.left = x + '%';
                s.style.top = y + '%';
                s.style.width = size + 'px';
                s.style.height = size + 'px';
                s.style.setProperty('--duration', duration + 's');

                container.appendChild(s);
                stars.push({ el: s, initialY: y, speed: speed });
            }

            // Анимация при скролле
            window.addEventListener('scroll', () => {
                const scrollY = window.scrollY;
                stars.forEach(star => {
                    if (star.speed === 0) return;
                    let newY = (star.initialY - (scrollY * star.speed * 0.2));
                    // Зацикливание фона
                    while (newY < -10) newY += 110;
                    while (newY > 110) newY -= 110;
                    star.el.style.top = newY + '%';
                });
            });
        });