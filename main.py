from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import random
import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "super_secret_key_2025"

# ========== ДАННЫЕ В ПАМЯТИ (без файлов) ==========
# Пользователи: {username: {'password': hash, 'role': str, 'balance': int, 'hints': dict}}
USERS = {
    'admin': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'role': 'admin',
        'balance': 10000,
        'hints': {'fifty': 2, 'remove_one': 2, 'call_friend': 1, 'freeze': 1}
    },
    'player': {
        'password': hashlib.sha256('player123'.encode()).hexdigest(),
        'role': 'user',
        'balance': 5000,
        'hints': {'fifty': 1, 'remove_one': 1, 'call_friend': 0, 'freeze': 0}
    }
}

# Рекорды: {username: {'score': int, 'prize': str, 'date': str}}
RECORDS = {}

# Вопросы (встроенные)
QUESTIONS = [
    {"question": "Сколько цветов в радуге?", "options": ["5", "6", "7", "8"], "answer": "7", "theme": "Природа",
     "difficulty": "Легкий"},
    {"question": "Кто написал 'Войну и мир'?", "options": ["Достоевский", "Толстой", "Чехов", "Пушкин"],
     "answer": "Толстой", "theme": "Литература", "difficulty": "Средний"},
    {"question": "Корабль пустыни — это?", "options": ["Верблюд", "Лошадь", "Слон", "Обезьяна"], "answer": "Верблюд",
     "theme": "Животные", "difficulty": "Легкий"},
    {"question": "Столица Франции?", "options": ["Лондон", "Берлин", "Мадрид", "Париж"], "answer": "Париж",
     "theme": "География", "difficulty": "Легкий"},
    {"question": "Кто изобрёл лампочку?", "options": ["Тесла", "Эдисон", "Ньютон", "Эйнштейн"], "answer": "Эдисон",
     "theme": "Наука", "difficulty": "Средний"},
    {"question": "Какая планета самая большая?", "options": ["Марс", "Юпитер", "Сатурн", "Нептун"], "answer": "Юпитер",
     "theme": "Космос", "difficulty": "Средний"},
    {"question": "Кто нарисовал Мону Лизу?", "options": ["Ван Гог", "Пикассо", "Да Винчи", "Рембрандт"],
     "answer": "Да Винчи", "theme": "Искусство", "difficulty": "Средний"},
    {"question": "Сколько игроков в футбольной команде?", "options": ["9", "10", "11", "12"], "answer": "11",
     "theme": "Спорт", "difficulty": "Легкий"},
    {"question": "Какой океан самый большой?", "options": ["Атлантический", "Индийский", "Северный Ледовитый", "Тихий"],
     "answer": "Тихий", "theme": "География", "difficulty": "Средний"},
    {"question": "Кто сыграл Джона Уика?", "options": ["Брюс Ли", "Джейсон Стэйтем", "Киану Ривз", "Том Круз"],
     "answer": "Киану Ривз", "theme": "Кино", "difficulty": "Средний"},
    {"question": "Формула воды?", "options": ["CO2", "NaCl", "H2O", "O2"], "answer": "H2O", "theme": "Наука",
     "difficulty": "Легкий"},
    {"question": "Самая высокая гора в мире?", "options": ["Эверест", "К2", "Эльбрус", "Мак-Кинли"],
     "answer": "Эверест", "theme": "География", "difficulty": "Средний"},
    {"question": "Кто спел 'Billie Jean'?", "options": ["Prince", "MJ", "Madonna", "Whitney"], "answer": "MJ",
     "theme": "Музыка", "difficulty": "Легкий"},
    {"question": "Сколько дней в високосном году?", "options": ["365", "366", "364", "367"], "answer": "366",
     "theme": "Общие", "difficulty": "Средний"},
    {"question": "Какая страна подарила миру пиццу?", "options": ["Франция", "Италия", "Испания", "Греция"],
     "answer": "Италия", "theme": "Еда", "difficulty": "Легкий"},
    {"question": "Символ Windows?", "options": ["Яблоко", "Пингвин", "Флаг", "Окно"], "answer": "Флаг",
     "theme": "Технологии", "difficulty": "Средний"},
    {"question": "Первая буква греческого алфавита?", "options": ["Бета", "Гамма", "Альфа", "Омега"], "answer": "Альфа",
     "theme": "Общие", "difficulty": "Легкий"},
    {"question": "Кто написал 'Гарри Поттера'?", "options": ["Толкин", "Роулинг", "Мартин", "Кинг"],
     "answer": "Роулинг", "theme": "Литература", "difficulty": "Легкий"},
    {"question": "Самый быстрый животное на суше?", "options": ["Лев", "Гепард", "Леопард", "Тигр"], "answer": "Гепард",
     "theme": "Животные", "difficulty": "Легкий"},
    {"question": "Столица Японии?", "options": ["Сеул", "Пекин", "Токио", "Бангкок"], "answer": "Токио",
     "theme": "География", "difficulty": "Легкий"},
]

# Несгораемые суммы
SAFE_SUMS = {0: 0, 4: 5000, 9: 32000, 14: 100000, 19: 500000}

# Магазин подсказок
SHOP_ITEMS = {
    'fifty': {'name': '🎯 50/50', 'price': 500, 'description': 'Убирает 2 неправильных ответа'},
    'remove_one': {'name': '🗑️ Убрать один', 'price': 300, 'description': 'Убирает 1 неправильный ответ'},
    'call_friend': {'name': '📞 Звонок другу', 'price': 800, 'description': 'Друг подскажет ответ (80%)'},
    'freeze': {'name': '⏰ Заморозка', 'price': 600, 'description': '+30 секунд к таймеру'},
    'extra_life': {'name': '❤️ Доп. жизнь', 'price': 1000, 'description': '+1 жизнь в игре'}
}


# ========== ФУНКЦИИ ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_balance(username):
    return USERS.get(username, {}).get('balance', 0)


def add_balance(username, amount):
    if username in USERS:
        USERS[username]['balance'] += amount
        return True
    return False


def remove_balance(username, amount):
    if username in USERS and USERS[username]['balance'] >= amount:
        USERS[username]['balance'] -= amount
        return True
    return False


def get_hints(username):
    return USERS.get(username, {}).get('hints', {'fifty': 0, 'remove_one': 0, 'call_friend': 0, 'freeze': 0})


def add_hint(username, hint_type):
    if username in USERS and hint_type in USERS[username]['hints']:
        USERS[username]['hints'][hint_type] += 1
        return True
    return False


def use_hint_in_game(username, hint_type):
    if username in USERS and USERS[username]['hints'].get(hint_type, 0) > 0:
        USERS[username]['hints'][hint_type] -= 1
        return True
    return False


def save_record(username, score, prize):
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    RECORDS[username] = {'score': score, 'prize': prize, 'date': date}


def get_leaderboard():
    sorted_records = sorted(RECORDS.items(), key=lambda x: x[1]['score'], reverse=True)
    return [{'username': name, 'score': data['score'], 'prize': data['prize'], 'date': data['date']}
            for name, data in sorted_records[:20]]


def get_user_best(username):
    if username in RECORDS:
        return RECORDS[username]
    return None


# ========== АДМИН-ФУНКЦИИ ==========
def add_user(username, password, role='user'):
    if username in USERS:
        return False
    USERS[username] = {
        'password': hash_password(password),
        'role': role,
        'balance': 1000,
        'hints': {'fifty': 1, 'remove_one': 1, 'call_friend': 0, 'freeze': 0}
    }
    return True


def delete_user(username):
    if username in USERS and username != 'admin':
        del USERS[username]
        return True
    return False


def get_all_users():
    return [{'username': u, 'role': USERS[u]['role'], 'balance': USERS[u]['balance']}
            for u in USERS]


def add_question(question, options, answer, theme, difficulty):
    QUESTIONS.append({
        'question': question,
        'options': options.split(','),
        'answer': answer,
        'theme': theme,
        'difficulty': difficulty
    })


def delete_question(index):
    if 0 <= index < len(QUESTIONS):
        QUESTIONS.pop(index)
        return True
    return False


def edit_question(index, question, options, answer, theme, difficulty):
    if 0 <= index < len(QUESTIONS):
        QUESTIONS[index] = {
            'question': question,
            'options': options.split(','),
            'answer': answer,
            'theme': theme,
            'difficulty': difficulty
        }
        return True
    return False


# ========== МАРШРУТЫ ==========
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    session['score'] = 0
    session['q_index'] = 0
    session['lives'] = 3
    session['fifty_used'] = False
    session['remove_one_used'] = False
    session['stats'] = {'correct': 0, 'wrong': 0, 'prizes': []}

    today = datetime.date.today().isoformat()
    if session.get('last_bonus') != today:
        session['daily_bonus'] = True
        session['last_bonus'] = today
    else:
        session['daily_bonus'] = False

    leaderboard = get_leaderboard()[:5]
    balance = get_balance(session['username'])
    hints = get_hints(session['username'])

    return render_template('index.html', total=len(QUESTIONS), lives=3,
                           daily_bonus=session['daily_bonus'], username=session['username'],
                           leaderboard=leaderboard, balance=balance, hints=hints)


@app.route('/shop')
def shop():
    if 'username' not in session:
        return redirect(url_for('login'))

    balance = get_balance(session['username'])
    hints = get_hints(session['username'])
    return render_template('shop.html', shop_items=SHOP_ITEMS, balance=balance, hints=hints)


@app.route('/buy-item', methods=['POST'])
def buy_item():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Не авторизован'})

    item_id = request.form.get('item_id')
    username = session['username']

    if item_id not in SHOP_ITEMS:
        return jsonify({'success': False, 'message': 'Товар не найден'})

    price = SHOP_ITEMS[item_id]['price']

    if remove_balance(username, price):
        if item_id == 'extra_life':
            # Добавляем жизнь в текущую сессию
            session['lives'] = session.get('lives', 3) + 1
        else:
            add_hint(username, item_id)
        return jsonify({'success': True, 'message': f'Куплено: {SHOP_ITEMS[item_id]["name"]}',
                        'new_balance': get_balance(username)})

    return jsonify({'success': False, 'message': 'Недостаточно средств!'})


@app.route('/game', methods=['GET', 'POST'])
def game():
    if 'username' not in session:
        return redirect(url_for('login'))

    idx = session.get('q_index', 0)
    total = len(QUESTIONS)
    lives = session.get('lives', 3)

    if lives <= 0:
        return redirect(url_for('result'))

    if idx >= total:
        return redirect(url_for('result'))

    q = QUESTIONS[idx]
    options = q['options'].copy()

    # Ежедневный бонус
    if session.get('daily_bonus') and request.method == 'GET':
        session['daily_bonus'] = False
        add_balance(session['username'], 500)
        add_hint(session['username'], 'fifty')
        return render_template('game.html', q=q, options=options,
                               num=idx + 1, total=total, fifty_used=session.get('fifty_used', False),
                               remove_one_used=session.get('remove_one_used', False),
                               lives=lives, score=session.get('score', 0), username=session['username'],
                               safe_sum=SAFE_SUMS.get(idx, 0), balance=get_balance(session['username']),
                               hints=get_hints(session['username']))

    # Подсказка 50/50 (из магазина)
    if request.method == 'POST' and 'fifty_fifty' in request.form:
        if use_hint_in_game(session['username'], 'fifty'):
            session['fifty_used'] = True
            correct = q['answer']
            wrong = [o for o in q['options'] if o != correct]
            if wrong:
                keep = random.choice(wrong[:1] if len(wrong) == 1 else [wrong[0]])
                options = [correct, keep]
                random.shuffle(options)
        else:
            return render_template('game.html', q=q, options=options,
                                   num=idx + 1, total=total, fifty_used=session.get('fifty_used', False),
                                   remove_one_used=session.get('remove_one_used', False),
                                   lives=lives, score=session.get('score', 0), username=session['username'],
                                   safe_sum=SAFE_SUMS.get(idx, 0), balance=get_balance(session['username']),
                                   hints=get_hints(session['username']), error='Нет подсказки 50/50!')

    # Подсказка "Убрать один"
    if request.method == 'POST' and 'remove_one' in request.form:
        if use_hint_in_game(session['username'], 'remove_one'):
            session['remove_one_used'] = True
            correct = q['answer']
            wrong = [o for o in q['options'] if o != correct]
            if wrong:
                to_remove = random.choice(wrong)
                options = [o for o in options if o != to_remove]
        else:
            return render_template('game.html', q=q, options=options,
                                   num=idx + 1, total=total, fifty_used=session.get('fifty_used', False),
                                   remove_one_used=session.get('remove_one_used', False),
                                   lives=lives, score=session.get('score', 0), username=session['username'],
                                   safe_sum=SAFE_SUMS.get(idx, 0), balance=get_balance(session['username']),
                                   hints=get_hints(session['username']), error='Нет подсказки "Убрать один"!')

    # Ответ на вопрос
    if request.method == 'POST' and 'answer' in request.form:
        user_answer = request.form['answer']
        if user_answer == q['answer']:
            session['score'] += 1
            session['stats']['correct'] += 1

            # Добавляем монеты за правильный ответ
            reward = 100
            add_balance(session['username'], reward)

            session['q_index'] += 1
        else:
            session['stats']['wrong'] += 1
            session['lives'] -= 1
            session['q_index'] += 1

        return redirect(url_for('game'))

    return render_template('game.html', q=q, options=options,
                           num=idx + 1, total=total, fifty_used=session.get('fifty_used', False),
                           remove_one_used=session.get('remove_one_used', False),
                           lives=lives, score=session.get('score', 0), username=session['username'],
                           safe_sum=SAFE_SUMS.get(idx, 0), balance=get_balance(session['username']),
                           hints=get_hints(session['username']), error=None)


@app.route('/result')
def result():
    if 'username' not in session:
        return redirect(url_for('login'))

    score = session.get('score', 0)
    total = len(QUESTIONS)
    lives = session.get('lives', 0)
    stats = session.get('stats', {'correct': 0, 'wrong': 0, 'prizes': []})

    last_safe = 0
    for q_num, amount in SAFE_SUMS.items():
        if score > q_num:
            last_safe = amount

    if score == total:
        prize = "1 000 000 ₽"
        msg = "🏆 МИЛЛИОНЕР! 🏆"
    else:
        prize = f"{last_safe:,} ₽".replace(',', ' ')
        if last_safe == 0:
            msg = "Вы ушли ни с чем 😢"
        else:
            msg = f"Ваш выигрыш: {prize}"

    # Сохраняем рекорд
    save_record(session['username'], score, prize)
    accuracy = (stats['correct'] / (stats['correct'] + stats['wrong']) * 100) if (stats['correct'] + stats[
        'wrong']) > 0 else 0

    return render_template('result.html', score=score, total=total, prize=prize,
                           message=msg, lives=lives, stats=stats, accuracy=round(accuracy, 1),
                           username=session['username'], balance=get_balance(session['username']))


@app.route('/leaderboard')
def leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    leaderboard = get_leaderboard()
    user_best = get_user_best(session['username'])

    return render_template('leaderboard.html', leaderboard=leaderboard,
                           username=session['username'], user_best=user_best,
                           balance=get_balance(session['username']))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USERS and USERS[username]['password'] == hash_password(password):
            session['username'] = username
            session['role'] = USERS[username]['role']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль!')

    return render_template('login.html', error=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            return render_template('register.html', error='Пароли не совпадают!')

        if len(password) < 4:
            return render_template('register.html', error='Пароль минимум 4 символа!')

        if username in USERS:
            return render_template('register.html', error='Пользователь уже существует!')

        add_user(username, password)
        return redirect(url_for('login'))

    return render_template('register.html', error=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    users = get_all_users()
    return render_template('admin_panel.html', users=users, questions=QUESTIONS, username=session['username'])


@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403

    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    if add_user(username, password, role):
        return jsonify({'success': True})
    return jsonify({'error': 'Пользователь уже существует'}), 400


@app.route('/admin/delete-user/<username>')
def admin_delete_user(username):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    if username != 'admin':
        delete_user(username)
    return redirect(url_for('admin_panel'))


@app.route('/admin/change-role/<username>/<role>')
def admin_change_role(username, role):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    if username in USERS and role in ['user', 'admin']:
        USERS[username]['role'] = role
    return redirect(url_for('admin_panel'))


@app.route('/admin/add-balance', methods=['POST'])
def admin_add_balance():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403

    username = request.form['username']
    amount = int(request.form['amount'])

    if username in USERS:
        add_balance(username, amount)
        return jsonify({'success': True})
    return jsonify({'error': 'Пользователь не найден'}), 400


@app.route('/admin/add-question', methods=['POST'])
def admin_add_question():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403

    question = request.form['question']
    options = request.form['options']
    answer = request.form['answer']
    theme = request.form['theme']
    difficulty = request.form['difficulty']

    add_question(question, options, answer, theme, difficulty)
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete-question/<int:index>')
def admin_delete_question(index):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))

    delete_question(index)
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    print("=" * 50)
    print("🎮 КТО ХОЧЕТ СТАТЬ МИЛЛИОНЕРОМ?")
    print("=" * 50)
    print(f"📊 ВСЕГО ВОПРОСОВ: {len(QUESTIONS)}")
    print(f"👑 АДМИН: admin / admin123")
    print(f"👤 ИГРОК: player / player123")
    print(f"💰 ЗА ПРАВИЛЬНЫЙ ОТВЕТ ДАЁТСЯ 100 МОНЕТ")
    print("=" * 50)
    app.run(debug=True)
else:
    pass