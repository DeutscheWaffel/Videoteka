document.addEventListener('DOMContentLoaded', function () {
    // --- Формы регистрации/входа ---
    function showForm(formId) {
        const forms = document.querySelectorAll('.form');
        forms.forEach(form => {
            if (form.classList.contains('active')) {
                form.classList.remove('active');
            }
        });
        const target = document.getElementById(formId);
        if (target) {
            target.classList.add('active');
        }
    }
    // Делаем функцию доступной глобально для inline-обработчиков в HTML
    window.showForm = showForm;

    const API_BASE = '/api/v1';

    async function apiRequest(path, options = {}) {
        const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
        const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
        const text = await res.text();
        let data;
        try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
        if (!res.ok) {
            const message = (data && (data.detail || data.message)) || 'Ошибка запроса';
            throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
        }
        return data;
    }

    // Привязываем обработчики к ссылкам
    document.querySelector('.login-link a')?.addEventListener('click', function(e) {
        e.preventDefault();
        showForm('loginForm');
    });

    document.querySelector('.register-link a')?.addEventListener('click', function(e) {
        e.preventDefault();
        showForm('registerForm');
    });

    document.getElementById('register')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorDiv = document.getElementById('error');

        if (password !== confirmPassword) {
            errorDiv.textContent = 'Пароли не совпадают!';
            errorDiv.classList.add('show');
            return;
        }

        try {
            await apiRequest('/register', {
                method: 'POST',
                body: JSON.stringify({ username, email, password })
            });
            // Покажем форму логина после успешной регистрации
            errorDiv.classList.remove('show');
            errorDiv.textContent = '';
            showForm('loginForm');
        } catch (err) {
            errorDiv.textContent = err.message || 'Ошибка регистрации';
            errorDiv.classList.add('show');
        }
    });

    document.getElementById('login')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const errorDiv = document.getElementById('loginError');

        if (!username || !password) {
            errorDiv.textContent = 'Заполните все поля!';
            errorDiv.classList.add('show');
            return;
        }

        try {
            const data = await apiRequest('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            if (data && data.access_token) {
                localStorage.setItem('token', data.access_token);
            }
            errorDiv.classList.remove('show');
            errorDiv.textContent = '';
            // После входа — на главную (из корня)
            window.location.href = '/all_html/home.html';
        } catch (err) {
            errorDiv.textContent = err.message || 'Ошибка входа';
            errorDiv.classList.add('show');
        }
    });

    // --- Логика для корзины и закладок ---
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    let bookmarks = JSON.parse(localStorage.getItem('bookmarks')) || [];

    // Функция для обновления localStorage
    function updateStorage() {
        localStorage.setItem('cart', JSON.stringify(cart));
        localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    }

    // Функция для добавления/удаления из корзины
    function toggleCart(movie) {
        const index = cart.findIndex(item => item.id === movie.id);
        const button = document.querySelector(`[data-id="${movie.id}"] .cart-btn`);

        if (index === -1) {
            cart.push(movie);
            button.textContent = '🛒';
            alert(`Фильм "${movie.title}" добавлен в корзину!`);
        } else {
            cart.splice(index, 1);
            button.textContent = '🛒';
            alert(`Фильм "${movie.title}" удалён из корзины!`);
        }
        updateStorage();
    }

    // Функция для добавления/удаления из закладок
    function toggleBookmark(movie) {
        const index = bookmarks.findIndex(item => item.id === movie.id);
        const button = document.querySelector(`[data-id="${movie.id}"] .bookmark-btn`);

        if (index === -1) {
            bookmarks.push(movie);
            button.textContent = '🔖';
            alert(`Фильм "${movie.title}" добавлен в закладки!`);
        } else {
            bookmarks.splice(index, 1);
            button.textContent = '🏷️';
            alert(`Фильм "${movie.title}" удалён из закладок!`);
        }
        updateStorage();
    }

    // Обработчики кликов для фильмов
    document.querySelectorAll('.movie-card').forEach(card => {
        const title = card.querySelector('.movie-title').textContent;
        const author = card.querySelector('.movie-author').textContent;
        const price = card.querySelector('.movie-price').textContent;
        const id = card.getAttribute('data-id');

        const movie = {
            id,
            title,
            author,
            price
        };

        card.querySelector('.cart-btn')?.addEventListener('click', function () {
            toggleCart(movie);
        });

        card.querySelector('.bookmark-btn')?.addEventListener('click', function () {
            toggleBookmark(movie);
        });

        // Обновляем статус кнопок при загрузке
        const cartBtn = card.querySelector('.cart-btn');
        const bookmarkBtn = card.querySelector('.bookmark-btn');

        if (cart.some(item => item.id === movie.id)) {
            cartBtn.textContent = '🛒';
        }

        if (bookmarks.some(item => item.id === movie.id)) {
            bookmarkBtn.textContent = '🔖';
        }
    });
});