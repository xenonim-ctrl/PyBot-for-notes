<h1 align="center">📔 Tarot & Dreams Diary Bot</h1>
<p align="center">
  <em>✨ Ваш личный ассистент для записи раскладов, снов, предчувствий и ритуалов ✨</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Aiogram-3.22.0-green.svg" alt="Aiogram Version">
  <img.shields.io/badge/PostgreSQL-Supported-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Telegram-Bot-blue.svg" alt="Telegram Bot">
</p>

<div align="center">

![Demo](https://via.placeholder.com/800x400.png?text=Telegram+Bot+Demo+Placeholder)

</div>

## 🌟 О проекте

Telegram бот для ведения личного дневника с поддержкой различных категорий записей:

- **🔮 Расклады Таро** - запись вопросов, карт и трактовок
- **💭 Сны** - фиксация и анализ сновидений  
- **🌀 Предчувствия** - интуитивные озарения и предчувствия
- **🕯️ Ритуалы** - описание магических практик и обрядов

## 🚀 Возможности

### 📝 Запись данных
- **Интуитивный интерфейс** с пошаговым заполнением
- **Разделение по категориям** для удобной организации
- **Автоматическое сохранение** даты и времени создания

### 👁️ Просмотр записей  
- **Агрегированный список** всех записей в хронологическом порядке
- **Умный поиск** по всем текстовым полям
- **Навигация стрелками** между записями

### 🛠️ Управление записями
- **📆 Перенос даты** - изменение времени создания записи
- **❌ Удаление** - полное удаление неактуальных записей
- **📄 Итоги** - добавление результатов и выводов к записям

### 🔒 Безопасность
- **Система белых списков** - доступ только для доверенных пользователей
- **Изоляция данных** - каждый пользователь видит только свои записи

## 🛠 Технологии

- **Python 3.8+** - основной язык программирования
- **Aiogram 3.x** - современный фреймворк для Telegram ботов
- **PostgreSQL** - надежное хранение данных
- **python-dotenv** - управление конфигурацией
- **Asyncio** - асинхронное программирование

<h2>📦 Установка и настройка</h2>

<h3>1. Клонирование репозитория</h3>
<pre><code>git clone https://github.com/xenonim-ctrl/PyBot-for-notes.git
cd tarot-diary-bot</code></pre>

<h3>2. Установка зависимостей</h3>
<pre><code>pip install -r requirements.txt</code></pre>

<h3>3. Настройка базы данных</h3>
<p>Убедитесь, что PostgreSQL запущен и создайте базу данных:</p>
<pre><code>CREATE DATABASE your_db_name;</code></pre>

<h3>4. Конфигурация</h3>
<p>Создайте или измените файл <code>.env</code> в корневой директории (для вашего удобства создан шаблон .env.example):</p>
<pre><code>BOT_TOKEN=your_telegram_bot_token_here
ALLOWED_USERS=123456789,987654321

DB_HOST=localhost
DB_NAME=name_db  
DB_USER=postgres
DB_PASS=your_password
DB_PORT=5432</code></pre>

<h3>5. Запуск бота</h3>
<pre><code>python main.py</code></pre>

<h2>🗃 Структура проекта</h2>
<pre>
tarot-diary-bot/
├── 🎯 bot.py              # Основной файл бота
├── 🗄️ db.py               # Работа с базой данных
├── 🛠️️ keyboards.py        # Клавиатуры
├── 🏗️ states.py           # Состояния FSM
├── 🛠️ functions.py        # Вспомогательные функции
├── 📦 requirements.txt    # Зависимости проекта
└── ⚙️ .env               # Конфигурация, у вас шаблон .env.example
</pre>

<h2>💾 База данных</h2>
<table>
  <tr>
    <th>Таблица</th>
    <th>Назначение</th>
  </tr>
  <tr>
    <td><strong>spreads</strong></td>
    <td>📊 Записи раскладов Таро</td>
  </tr>
  <tr>
    <td><strong>dreams</strong></td>
    <td>💭 Записи сновидений</td>
  </tr>
  <tr>
    <td><strong>premonitions</strong></td>
    <td>🌪️ Интуитивные предчувствия</td>
  </tr>
  <tr>
    <td><strong>rituals</strong></td>
    <td>🕯️ Магические ритуалы</td>
  </tr>
  <tr>
    <td><strong>results</strong></td>
    <td>📄 Итоги и выводы</td>
  </tr>
</table>

<h2>🔧 Кастомизация</h2>

<h4>Добавление новой категории:</h4>
<ol>
  <li>Добавьте таблицу в БД</li>
  <li>Обновите <code>CATEGORY_TABLE</code> в functions.py</li>
  <li>Создайте состояния FSM в states.py</li>
  <li>Добавьте обработчики в main.py</li>
</ol>

<h4>Настройка прав доступа:</h4>
<p>Отредактируйте <code>ALLOWED_USERS</code> в .env файле:</p>
<pre><code>ALLOWED_USERS=***</code></pre>

<div align="center">
  <h2>⭐ Если вам понравился этот проект, не забудьте поставить звезду! ⭐</h2>
  <p><em>С любовью для магического сообщества 💫</em></p>
</div>
<div align="center">
<img src="https://img.icons8.com/color/96/000000/tarot-cards.png" width="64" height="64"/> <img src="https://img.icons8.com/color/96/000000/magic-crystal-ball.png" width="64" height="64"/></div>

