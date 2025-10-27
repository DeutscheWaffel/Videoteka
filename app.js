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

	const API_BASE = (() => {
		// Если страница открыта как file:// — используем локальный сервер FastAPI
		if (window.location.protocol === 'file:') {
			return 'http://localhost:8000/api/v1';
		}
		// Иначе — работаем от текущего origin
		return `${window.location.origin}/api/v1`;
	})();

	async function apiRequest(path, options = {}) {
		const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
		const token = localStorage.getItem('token');
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}
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
			// После входа — на главную (корень статики)
			window.location.href = '/home.html';
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

    // --- Работа с серверными закладками ---
    async function fetchBookmarksFromServer() {
        try {
            const data = await apiRequest('/bookmarks');
            // Конвертируем к прежнему формату для совместимости UI
            bookmarks = data.map(b => ({ id: b.movie_id, title: b.title, author: b.author || '', price: b.price || '' }));
            updateStorage();
            return bookmarks;
        } catch (e) {
            // Если не авторизованы — молча игнорируем, оставляем локальные
            return bookmarks;
        }
    }

    async function addBookmarkOnServer(movie) {
        return apiRequest('/bookmarks', {
            method: 'POST',
            body: JSON.stringify({ movie_id: movie.id, title: movie.title, author: movie.author, price: movie.price })
        });
    }

    async function removeBookmarkOnServer(movieId) {
        return apiRequest(`/bookmarks/${movieId}`, { method: 'DELETE' });
    }

    // --- Работа с серверной корзиной ---
    async function fetchCartFromServer() {
        try {
            const data = await apiRequest('/cart');
            cart = data.map(c => ({ id: c.movie_id, title: c.title, author: c.author || '', price: c.price || '' }));
            updateStorage();
            return cart;
        } catch (e) {
            return cart;
        }
    }

    async function addCartOnServer(movie) {
        return apiRequest('/cart', {
            method: 'POST',
            body: JSON.stringify({ movie_id: movie.id, title: movie.title, author: movie.author, price: movie.price })
        });
    }

    async function removeCartOnServer(movieId) {
        return apiRequest(`/cart/${movieId}`, { method: 'DELETE' });
    }

    // Функция для добавления/удаления из корзины
    async function toggleCart(movie) {
        const index = cart.findIndex(item => item.id === movie.id);
        const button = document.querySelector(`[data-id="${movie.id}"] .cart-btn`);

        try {
            if (index === -1) {
                await addCartOnServer(movie);
                cart.push(movie);
                button.textContent = 'Удалить из корзины';
                alert(`Фильм "${movie.title}" добавлен в корзину!`);
            } else {
                await removeCartOnServer(movie.id);
                cart.splice(index, 1);
                button.textContent = 'Добавить в корзину';
                alert(`Фильм "${movie.title}" удалён из корзины!`);
            }
            updateStorage();
        } catch (e) {
            alert(e.message || 'Ошибка работы с корзиной');
        }
    }

    // Функция для добавления/удаления из закладок
    async function toggleBookmark(movie) {
        const index = bookmarks.findIndex(item => item.id === movie.id);
        const button = document.querySelector(`[data-id="${movie.id}"] .bookmark-btn`);

        try {
            if (index === -1) {
                await addBookmarkOnServer(movie);
                bookmarks.push(movie);
                button.textContent = 'Удалить из закладок';
            } else {
                await removeBookmarkOnServer(movie.id);
                bookmarks.splice(index, 1);
                button.textContent = 'Добавить в закладки';
            }
            updateStorage();
        } catch (e) {
            alert(e.message || 'Ошибка работы с закладками');
        }
    }

    // Делегирование событий для динамически загружаемых карточек
    document.body.addEventListener('click', async (e) => {
        const cartBtn = e.target.closest('.cart-btn');
        const bookmarkBtn = e.target.closest('.bookmark-btn');
        if (!cartBtn && !bookmarkBtn) return;

        const card = e.target.closest('.movie-card');
        if (!card) return;
        const title = card.querySelector('.movie-title')?.textContent || '';
        const author = card.querySelector('.movie-author')?.textContent || '';
        const price = card.querySelector('.movie-price')?.textContent || '';
        const id = card.getAttribute('data-id');
        const movie = { id, title, author, price };

        if (cartBtn) {
            await toggleCart(movie);
        }
        if (bookmarkBtn) {
            await toggleBookmark(movie);
        }
    });

    // При загрузке страницы подтянем корзину и закладки для корректной иконки
    fetchCartFromServer();
    fetchBookmarksFromServer();

    // --- Каталог жанров: переход на страницу жанра ---
    document.querySelectorAll('#genreList .genre-item').forEach(item => {
        item.addEventListener('click', function () {
            const genre = item.getAttribute('data-genre');
            if (!genre) return;
            // Страница жанра: /genre-<name>.html
            window.location.href = `/genre-${genre}.html`;
        });
    });
});