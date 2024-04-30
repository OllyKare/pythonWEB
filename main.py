import vk_api
from vk_api import keyboard
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import requests
from vk_api.keyboard import VkKeyboardColor
from sqlalchemy.sql import func
from datetime import date
from data import db_session
from data import __all_models

TOKEN = "vk1.a.MYPp6GnzVgrCd0EkM4EUfTJ68T-Pp0DrSroJaL9uVlUs3SUHxBnBTyfeP3BwisN3r73ODTwN8oStbwOrfI17gZC6tcZ2nI8LyzJG8C8dM5UTGy5V-JrPjn47UVcOFsDMjAO6AdfYdlAyfh4VVeqBv_Hp2TOTNiYsWhhwEZdlG9dl8xK6A7CZek6U1bM9yy_bY_5sFIZZ5CZk2dq8RfnLRw"
id_group = 225749075
db_session.global_init("db/bot_vk.db")
db_sess = db_session.create_session()


def show_list_all_time(user):
    a = __all_models.Payments.summa
    b = __all_models.Payments.title
    c = __all_models.Payments.created_date
    show_list = db_sess.query(a, b, func.strftime('%d.%m.%Y', c)).filter(__all_models.Payments.user_id == user).all()
    new_list = []
    for i in show_list:
        stroka = str(i[0]) + ' ' + i[1] + ' ' + i[2]
        new_list.append(stroka)
    return new_list


def show_list_today(user):
    a = __all_models.Payments.summa
    b = __all_models.Payments.title
    show_list = db_sess.query(a, b).filter(__all_models.Payments.user_id == user,
                                           func.DATE(__all_models.Payments.created_date) == date.today()).all()
    new_list = []
    for i in show_list:
        stroka = str(i[0]) + ' ' + i[1]
        new_list.append(stroka)
    return new_list


def show_list_week(user):
    a = __all_models.Payments.summa
    b = __all_models.Payments.title
    c = __all_models.Payments.created_date
    show_list = db_sess.query(a, b, func.strftime('%d.%m.%Y', c)).filter(__all_models.Payments.user_id == user,
                                                                         func.strftime('%Y-%W', c) == func.strftime(
                                                                             '%Y-%W', func.now())).all()
    new_list = []
    for i in show_list:
        stroka = str(i[0]) + ' ' + i[1] + ' ' + i[2]
        new_list.append(stroka)
    return new_list


def show_list_month(user):
    a = __all_models.Payments.summa
    b = __all_models.Payments.title
    c = __all_models.Payments.created_date
    show_list = db_sess.query(a, b, func.strftime('%d.%m.%Y', c)).filter(__all_models.Payments.user_id == user,
                                                                         func.strftime('%Y-%m', c) == func.strftime(
                                                                             '%Y-%m', func.now())).all()
    new_list = []
    for i in show_list:
        stroka = str(i[0]) + ' ' + i[1] + ' ' + i[2]
        new_list.append(stroka)
    return new_list


def change_balance(user, message):
    payment = __all_models.Payments()
    payment.summa = message[0]
    payment.user_id = user
    payment.title = ' '.join(message[1:])
    db_sess.add(payment)
    db_sess.commit()


def add_card(user, message):
    card = __all_models.Cards()
    card.user_id = user
    card.title = message
    db_sess.add(card)
    db_sess.flush()
    db_sess.refresh(card)
    db_sess.commit()
    card_id = card.id
    return card_id


def get_card(vk, user, message):
    result = db_sess.query(__all_models.Cards.id).filter(__all_models.Cards.user_id == user,
                                                         __all_models.Cards.title == message).all()
    if result:
        result = result[-1]
        upload = vk_api.VkUpload(vk)
        photo = upload.photo_messages(f'photo/{result[0]}.jpg')
        owner_id = photo[0]['owner_id']
        photo_id = photo[0]['id']
        access_key = photo[0]['access_key']
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
        return attachment
    else:
        return ''


def save_photo(card_id, photo_url):
    r = requests.get(photo_url, allow_redirects=True)
    open(f'photo/{card_id}.jpg', 'wb').write(r.content)


def balance(user):
    balance = db_sess.query(func.sum(__all_models.Payments.summa)).filter(__all_models.Payments.user_id == user).first()
    return balance[0]


def send_message(vk, message, user_id, kb, att=None):
    vk.messages.send(user_id=user_id,
                     message=message,
                     keyboard=kb,
                     random_id=random.randint(0, 2 ** 64),
                     attachment=att)


def get_keyboard():
    kb = keyboard.VkKeyboard()
    kb.add_button("Мои финансы за все время", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("За день", color=VkKeyboardColor.PRIMARY)
    kb.add_button("За неделю", color=VkKeyboardColor.PRIMARY)
    kb.add_button("За месяц", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("Мой баланс", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("Баланс в €", color=VkKeyboardColor.NEGATIVE)
    kb.add_button("Баланс в $", color=VkKeyboardColor.NEGATIVE)
    kb.add_button("Баланс в ₿", color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()


def currency(value, user):
    money = balance(user)
    if money:
        url = f"https://api.coingate.com/v2/rates/merchant/{value}/RUB"
        result = requests.get(url=url)
        return money / float(result.text)
    else:
        return 0


def main():
    vk_session = vk_api.VkApi(
        token=TOKEN)

    longpoll = VkBotLongPoll(vk_session, id_group)
    kb = get_keyboard()

    for event in longpoll.listen():

        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.obj.message['text']
            vk = vk_session.get_api()
            user_id = event.obj.message['from_id']
            if message == "":
                att = event.obj.message['attachments'][0]
                if att['type'] == 'sticker':
                    sticker_id = att['sticker']['sticker_id']
                    try:
                        vk.messages.send(user_id=user_id,
                                         sticker_id=sticker_id,
                                         random_id=random.randint(0, 2 ** 64))
                    except BaseException:
                        send_message(vk, f"Я так не умею(((", user_id, kb)
            elif event.obj.message['attachments']:
                if event.obj.message['attachments'][0]['type'] == 'photo':
                    card_id = add_card(user_id, message)
                    photo_url = event.obj.message['attachments'][0]['photo']['sizes'][-1]['url']
                    save_photo(card_id, photo_url)
                    send_message(vk, "Карта успешно добавлена! Чтобы получить карту, напишите ее название!",
                                 user_id, kb)
            elif message[0] == '+' or message[0] == '-':
                message = message.split()
                if message[0][1:].isdigit():
                    change_balance(user_id, message)
                    send_message(vk, "Данные записаны и учтены!", user_id, kb)
                else:
                    send_message(vk, "Вы что-то перепутали! Проверьте правильность введенной суммы:)", user_id, kb)
            elif message == "Мой баланс":
                b = balance(user_id)
                if b:
                    send_message(vk, f"Ваш баланс: {b}", user_id, kb)
                else:
                    send_message(vk, f"Я ничего не знаю о ваших доходах и расходах!", user_id, kb)
            elif message == "Мои финансы за все время":
                a = '\n'
                slat = show_list_all_time(user_id)
                if slat:
                    send_message(vk, f"Ваши финансы за все время:{a}{a.join(slat)}", user_id, kb)
                else:
                    send_message(vk, f"Ура! Вы все еще не потратили ни рубля!", user_id, kb)
            elif message == "За день":
                a = '\n'
                slt = show_list_today(user_id)
                if slt:
                    send_message(vk, f"Ваши финансы за день:{a}{a.join(slt)}", user_id, kb)
                else:
                    send_message(vk, f"Ура! Вы сегодня еще не тратили деньги!", user_id, kb)
            elif message == "За неделю":
                a = '\n'
                slw = show_list_week(user_id)
                if slw:
                    send_message(vk, f"Ваши финансы за неделю:{a}{a.join(slw)}", user_id, kb)
                else:
                    send_message(vk, f"Невероятно! Вы ничего не купили на этой неделе!", user_id, kb)
            elif message == "За месяц":
                a = '\n'
                slm = show_list_month(user_id)
                if slm:
                    send_message(vk, f"Ваши финансы за месяц:{a}{a.join(slm)}", user_id, kb)
                else:
                    send_message(vk, f"Ого! Как можно ничего не купить за месяц!?", user_id, kb)
            elif message == "Баланс в €":
                send_message(vk, "Ваш баланс в €: {:.2f}".format(currency('EUR', user_id)), user_id, kb)
            elif message == "Баланс в $":
                send_message(vk, "Ваш баланс в $: {:.2f}".format(currency('USD', user_id)), user_id, kb)
            elif message == "Баланс в ₿":
                send_message(vk, "Ваш баланс в ₿: {:.8f}".format(currency('BTC', user_id)), user_id, kb)
            elif message == "Начать":
                send_message(vk, f"""Приветствую! С чего начнем? 
                                     Предалагаю внести первое изменение в вашем бюджете!""", user_id, kb)
            else:
                att = get_card(vk, user_id, message)
                if att:
                    send_message(vk, "Держите!", user_id, kb, att)
                else:
                    if message == "Спасибо!":
                        send_message(vk, "Пожалуйста!:)", user_id, kb)
                    else:
                        send_message(vk, "Увы, такой карты у вас нет(", user_id, kb)


if __name__ == '__main__':
    main()
