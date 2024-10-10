import telebot
from telebot import types
import random
from fpdf import FPDF
import os

bot_token = '6340359911:AAF7O0PUEsuwPvCtXvLSWNRRlJ0idjgwy1A'
bot = telebot.TeleBot(bot_token)

password = '2006'
authorized_users = {}
owner_id = [151114945]
tests = {}

def check_authorization(message):
    chat_id = message.chat.id
    if chat_id not in authorized_users or authorized_users[chat_id] != 'authorized':
        bot.send_message(chat_id, 'Botdan foydalanishni boshlash uchun parolni kiriting:')
        bot.register_next_step_handler(message, check_password)
        return False
    return True

def is_owner(user_id):
    return user_id in owner_id

def check_password(message):
    chat_id = message.chat.id
    if message.text == password:
        authorized_users[chat_id] = 'authorized'
        bot.send_message(chat_id, 'Avtorizatsiya muvaffaqiyatli boldi. Endi siz botdan foydalanishingiz mumkin')
        send_main_menu(chat_id)
    else:
        bot.send_message(chat_id, 'Notogri parol.')

def send_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    solve_test_button = types.KeyboardButton("Test yechish")
    keyboard.add(solve_test_button)
    
    if is_owner(chat_id):
        add_test_button = types.KeyboardButton("Test qo'shish")
        finish_test_button = types.KeyboardButton("Testni yakunlash")
        list_tests_button = types.KeyboardButton("Testlar ro'yxati")
        set_password_button = types.KeyboardButton("Parolni o'zgartirish")
        keyboard.add(add_test_button, finish_test_button)
        keyboard.add(list_tests_button, set_password_button)

    bot.send_message(chat_id, "Kerakli amalni tanlang:", reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if not check_authorization(message):
        return
    send_main_menu(chat_id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    if message.text == "Test yechish":
        solve_test(message)
    elif message.text == "Test qo'shish":
        if is_owner(message.from_user.id):
            add_test(message)
    elif message.text == "Testni yakunlash":
        if is_owner(message.from_user.id):
            finish_test(message)
    elif message.text == "Testlar ro'yxati":
        if is_owner(message.from_user.id):
            list_tests(message)
    elif message.text == "Parolni o'zgartirish":
        if is_owner(message.from_user.id):
            set_password(message)
    else:
        bot.send_message(chat_id, "Noto'g'ri buyruq. Iltimos, mavjud tugmalardan foydalaning.")

def set_password(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return
    bot.send_message(chat_id, 'Yangi parolni kiriting:')
    bot.register_next_step_handler(message, change_password)

def change_password(message):
    chat_id = message.chat.id
    new_password = message.text
    global password
    password = new_password
    bot.send_message(chat_id, 'Parol muvaffaqiyatli ozgartirildi.')
    send_main_menu(chat_id)

def add_test(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return
    bot.send_message(chat_id, 'Test nomini kiriting:')
    bot.register_next_step_handler(message, add_test_title)

def add_test_title(message):
    chat_id = message.chat.id
    test_title = message.text
    if not test_title.isalpha():
        bot.send_message(chat_id, 'Nom notogri. Qaytadan boshlang va test nomini raqamlar yoki maxsus belgilarsiz matnga kiriting. (lotin alifbosida)')
        send_main_menu(chat_id)
        return
    bot.send_message(chat_id, 'Toʻgʻri javoblarni vergul yordamida ajratib yuboring:\nMasalan: a,b,c,d')
    bot.register_next_step_handler(message, add_test_answers, test_title)

def add_test_answers(message, test_title):
    chat_id = message.chat.id
    test_answers = message.text.lower()
    if not all(answer.isalpha() and len(answer) == 1 for answer in test_answers.split(',')):
        bot.send_message(chat_id, 'Javoblar notogri formatda kiritilgan❌. Javoblarni faqat a,b,c,d formatida kiriting.')
        send_main_menu(chat_id)
        return
    bot.send_message(chat_id, 'Testning PDF faylini yuboring: \n (Ushbu PDF hujjatda test savollari boʻlishi kerak!)')
    bot.register_next_step_handler(message, add_test_pdf, test_title, test_answers)

def add_test_pdf(message, test_title, test_answers):
    chat_id = message.chat.id
    if message.document.mime_type != 'application/pdf':
        bot.send_message(chat_id, 'Men faqat PDF formatidagi fayllarni qabul qilaman❌. Iltimos, faylni PDF formatida yuboring.')
        send_main_menu(chat_id)
        return
    test_id = generate_test_id()
    save_test(test_id, test_title, test_answers, message.from_user.id)
    tests[test_id]['pdf'] = message.document.file_id
    bot.send_message(chat_id, f'Test muvaffaqiyatli kiritildi.\nTest 🆔:\n{test_id}')
    send_main_menu(chat_id)

def solve_test(message):
    chat_id = message.chat.id
    if not check_authorization(message):
        return
    bot.send_message(chat_id, 'Ismingizni kiriting:')
    bot.register_next_step_handler(message, solve_test_username)

def solve_test_username(message):
    chat_id = message.chat.id
    username = message.text
    if not username.isascii():
        bot.send_message(chat_id, 'Ism notogri. Qaytadan boshlang va raqam yoki maxsus belgilarsiz matnga ismingizni kiriting. (lotin alifbosida)')
        send_main_menu(chat_id)
        return
    bot.send_message(chat_id, 'Familiyani kiriting:')
    bot.register_next_step_handler(message, solve_test_usersurname, username)

def solve_test_usersurname(message, username):
    chat_id = message.chat.id
    usersurname = message.text
    if not usersurname.isascii():
        bot.send_message(chat_id, 'Familiya notogri. Qaytadan boshlang va raqam yoki maxsus belgilarsiz matnga ismingizni kiriting. (lotin alifbosida)')
        send_main_menu(chat_id)
        return
    bot.send_message(chat_id, 'Test ID`sini kiriting:')
    bot.register_next_step_handler(message, solve_test_id, username, usersurname)

def solve_test_id(message, username, usersurname):
    chat_id = message.chat.id
    test_id = message.text
    if not test_id.isdigit():
        bot.send_message(chat_id, 'Yaroqsiz ID❌.')
        send_main_menu(chat_id)
        return
    test_id = int(test_id)
    test = get_test(test_id)
    if test:
        bot.send_document(chat_id, test['pdf'])
        bot.send_message(chat_id, 'Testga javoblaringizni yuboring: \n Masalan: a,b,c,d')
        bot.register_next_step_handler(message, solve_test_answers, test, username, usersurname)
    else:
        bot.send_message(chat_id, 'Test topilmadi❌. Yana bir bor urinib ko `ring.')
        send_main_menu(chat_id)

def solve_test_answers(message, test, username, usersurname):
    chat_id = message.chat.id
    answers = message.text.lower()
    correct_answers = test['answers']
    result = calculate_score(answers, correct_answers)
    student = {
        'username': username,
        'usersurname': usersurname,
        'result': result
    }
    test['students'].append(student)
    bot.send_message(chat_id, f'Ism: {username}\nFamiliya: {usersurname}\nTest natijasi: {result}')
    send_main_menu(chat_id)

def finish_test(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return
    bot.send_message(chat_id, 'Testga ID`sini kiriting:')
    bot.register_next_step_handler(message, finish_test_id)

def finish_test_id(message):
    chat_id = message.chat.id
    test_id = message.text
    if not test_id.isdigit():
        bot.send_message(chat_id, 'Yaroqsiz ID❌. Qaytadan boshlang va test ID`sini togri kiriting.')
        send_main_menu(chat_id)
        return
    test_id = int(test_id)
    test = get_test(test_id)
    if test:
        if test['author'] != message.from_user.id:
            send_main_menu(chat_id)
            return
        sorted_students = sorted(test['students'], key=lambda student: student['result'], reverse=True)

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 10, f'Test ID {test_id}', 0, 1, 'C')
        pdf.ln(10)
        col_width = pdf.w / 3.2
        pdf.cell(col_width, 10, 'Ism', border=1)
        pdf.cell(col_width, 10, 'Familiya', border=1)
        pdf.cell(col_width, 10, 'Natija', border=1)
        pdf.ln(10)
        for student in sorted_students:
            pdf.cell(col_width, 10, student['username'], border=1)
            pdf.cell(col_width, 10, student['usersurname'], border=1)
            pdf.cell(col_width, 10, str(student['result']), border=1)
            pdf.ln(10)
        pdf_path = os.path.join(os.getcwd(), f'tests/results_{test_id}.pdf')
        pdf.output(pdf_path, 'F')
        bot.send_document(chat_id, open(pdf_path, 'rb'))
        bot.send_message(chat_id, 'Sinov muvaffaqiyatli yakunlandi. Test natijalari sizga PDF fayl korinishda yuborildi.')
    else:
        bot.send_message(chat_id, 'Test topilmadi❌. Yana bir bor urinib ko`ring.')
    send_main_menu(chat_id)

def list_tests(message):
    chat_id = message.chat.id
    if not is_owner(message.from_user.id):
        return

    if not tests:
        bot.send_message(chat_id, 'Hali testlar yoq❌. Yangi testlarni qoshing.')
        send_main_menu(chat_id)
        return

    for test_id, test_data in tests.items():
        test_info_message = f"🆔 {test_id}: {test_data['title']}"
        bot.send_message(chat_id, test_info_message)
        bot.send_document(chat_id, test_data['pdf'], caption=f"🆔 {test_id}: {test_data['title']}")
    
    send_main_menu(chat_id)

def generate_test_id():
    return random.randint(1000, 9999)

def get_test(test_id):
    return tests.get(test_id)

def save_test(test_id, test_title, test_answers, author_id):
    if test_id in tests:
        bot.send_message(chat_id, f'{test_id}-ID bilan test allaqachon mavjud. Boshqasini tanlang 🆔.')
        return  
    tests[test_id] = {
        'title': test_title,
        'answers': test_answers,
        'students': [],
        'author': author_id
    }

def calculate_score(answers, correct_answers):
    user_answers = [answer.strip() for answer in answers.split(',')]
    correct_answers_array = [answer.strip() for answer in correct_answers.split(',')]
    score = sum(1 for answer in user_answers if answer in correct_answers_array)
    return score

print("Bot muvaffaqiyatli ishga tushirildi!")

bot.polling()
