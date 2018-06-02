# -*- coding: utf-8 -*-

import sys, traceback, time, telebot, random, requests
import xl
import json
import wget,os
import lxml.html as lhtml
from telebot import types
from telegram.ext import Updater
import datetime
import time
import shutil
import smtplib
from telebot.types import LabeledPrice
#python -mwebbrowser "http://localhost:8000/cgi-bin/get_id.py?id=3&day=49"
token=""

bot = telebot.TeleBot(token)

u = Updater(token)

j = u.job_queue
j.start()

user_dict = {}
hide_mark=types.ReplyKeyboardRemove()

class User:
    def __init__(self, form_number):
        self.form_number = form_number;
        self.for_who = None;
        self.question_list_scores = xl.get_question_list(); #список вопросов с оценками на них
        self.question_list_ansewers = {}; #список вопросов с ответами пользователя
        for i in list(self.question_list_scores):
            self.question_list_ansewers.update({str(i):"Нет"}) #Забитый НЕТ сразу
        #print(self.question_list_ansewers.items())
        self.question_position = None; #номер вопроса на котором пользователь
        self.commentary = None;
        self.how_to_pay = None;
        self.email = None;
        self.name = None;
        self.phone = None;

def process_commentary_step(message):
    if message.text!="Назад":
        chat_id = message.chat.id
        commentary = message.text;
            
        user = user_dict[chat_id];
        user.commentary = commentary;
        
        print(user.commentary)
        
        body = "Выберете варианты оплаты\n\n1) Я хочу оплатить по фактуре в течении 14 дней после выполнения заказа\n2) Я хочу чтобы вы сами списали с моего счета деньги согласно фактуры \n3) Я буду оплачивать наличными в офисе\n4) У меня есть абонемент на ваши услуги"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="1")
        button_2 = types.KeyboardButton(text="2")
        button_3 = types.KeyboardButton(text="3")
        button_4 = types.KeyboardButton(text="4")
        button_back = types.KeyboardButton(text="Назад")
        
        keyboard_.add(button_1, button_2, button_3, button_4)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
        bot.register_next_step_handler(message, process_how_to_pay_step)
    else:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def process_how_to_pay_step(message):
    if message.text!="Назад":
        chat_id = message.chat.id
        how_to_pay = message.text;
            
        user = user_dict[chat_id];
        user.how_to_pay = how_to_pay;
        
        print(user.how_to_pay)
        
        body = "Ваше Имя и Фамилия"
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=hide_mark)
        bot.register_next_step_handler(message, process_name_step)
    else:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def process_name_step(message):
    chat_id = message.chat.id
    name = message.text;
        
    user = user_dict[chat_id];
    user.name = name;
    
    body = "Телефон"
    
    bot.send_message(chat_id=message.chat.id, text=body)
    bot.register_next_step_handler(message, process_phone_step)

def process_phone_step(message):
    chat_id = message.chat.id
    phone = message.text;
    
    user = user_dict[chat_id]
    user.phone = phone
    
    body = "Почта"
    
    bot.send_message(chat_id=message.chat.id, text=body)
    bot.register_next_step_handler(message, process_email_step)

def process_email_step(message):
    chat_id = message.chat.id
    email = message.text;
    
    user = user_dict[chat_id]
    user.email = email
    
    score = 0;
    
    ############CALCULATE###############
    
    for i in user.question_list_scores.keys():
        for j in user.question_list_ansewers.keys():
            if i==j:
                if user.question_list_ansewers[j]=="Да":
                    score += user.question_list_scores[i]
    
    ####################################
    print("scores", score)
    
    result = xl.check_difficult(score, user.form_number, user.for_who);
    
    t_form = "";
    if user.form_number=="1":
        t_form = "P"
    elif user.form_number=="2":
        t_form = "M"
    elif user.form_number=="3":
        t_form = "C"
    #########EMAIL FORM#############
    
    email_text = "Вам необходимо подавать декларацию формы "+t_form+". Сложность вашей декларации определена - "+result['name']+". Цена "+str(result['w_nds'])+"€ без НДС "+str(result['nds'])+"€ в т.ч. НДС\nПодробнее ниже:\n\n"
    
    email_text+="\nИмя: "+user.name;
    email_text+="\nТелефон: "+user.phone;
    email_text+="\nПочта: "+user.email+"\n\n";
    
    for i in user.question_list_scores.keys():
        for j in user.question_list_ansewers.keys():
            if i==j:
                if user.question_list_ansewers[j]=="Да":
                    email_text+=i+" - Да\n"
    
    email_text+="\nCуммарное колличество балов за вопросы: "+str(score)+"\n\n";

    if user.how_to_pay=="1":
        email_text+='Пользователь выбрал тип оплаты  "Я хочу оплатить по фактуре в течении 14 дней после выполнения заказа"\n'
    elif user.how_to_pay=="2":
        email_text+='Пользователь выбрал тип оплаты  "Я хочу чтобы вы сами списали с моего счета деньги согласно фактуры"\n'
    elif user.how_to_pay=="3":
        email_text+='Пользователь выбрал тип оплаты  "Я буду оплачивать наличными в офисе"\n'
    elif user.how_to_pay=="4":
        email_text+='Пользователь выбрал тип оплаты  "У меня есть абонемент на ваши услуги"\n'
    
    if user.commentary!="Дальше":
        email_text+="\nКомментарий: "+user.commentary;
    else:
        email_text+="\nКомментарий: Пользователь не оставлял комментарий";
    
    ################################
    body = "Вам необходимо подавать декларацию формы "+t_form+". Сложность вашей декларации определена - "+result['name']+". Цена "+str(result['w_nds'])+"€ без НДС "+str(result['nds'])+"€ в т.ч. НДС"
    
    keyboard_ = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    button_1 = types.KeyboardButton(text="Дальше")
    button_2 = types.KeyboardButton(text="Назад")
    
    keyboard_.add(button_1)
        
    bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
    print(user_dict[chat_id].name, user_dict[chat_id].phone, user_dict[chat_id].email)
    bot.register_next_step_handler(message, process_end_step)
    try:
        xl.send_all(email_text, email);
    except:
        pass

def process_end_step(message):
    if message.text!="Назад":
        chat_id = message.chat.id
        form_number = message.text;
            
        user = user_dict[chat_id]
        
        body = "Ваш заказ принят.\n\nПожалуйста, ожидайте информацию на почту"

        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
    else:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def process_form_step(message):
    if message.text!="Назад":
        chat_id = message.chat.id
        form_number = message.text;
        
        user = User(form_number);
            
        user_dict[chat_id] = user;
        
        body = "Для кого?"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="На одного")
        button_2 = types.KeyboardButton(text="На семью")
        button_back = types.KeyboardButton(text="Назад")
        
        keyboard_.add(button_1, button_2)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
        bot.register_next_step_handler(message, process_for_who_step)
    else:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def process_for_who_step(message):
    if message.text!="Назад":
        chat_id = message.chat.id
        for_who = message.text;
        
        user = user_dict[chat_id]
        user.for_who = for_who
        user.question_position = 1;
        
        q_text = list(user.question_list_scores)[0];
        
        body = "У вас будет возможность оставить комментарий после ответов на все вопросы чек листа.\n\nОтветьте на вопрос:\n\n"+q_text
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Да")
        button_2 = types.KeyboardButton(text="Нет")
        button_back = types.KeyboardButton(text="Назад")
        
        keyboard_.add(button_1, button_2)
        
        print(user_dict[chat_id].for_who, user_dict[chat_id].form_number, user_dict[chat_id].question_list_scores)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
        bot.register_next_step_handler(message, process_question_from_file_step)
    else:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def process_question_from_file_step(message):
    chat_id = message.chat.id
    email = message.text;
    
    user = user_dict[chat_id]
    
    if user.question_position<=len(list(user.question_list_scores))-1:
        q_to_update_key = list(user.question_list_scores)
        
        user.question_list_ansewers.update({q_to_update_key[user.question_position-1]:message.text})
        
        q_text = list(user.question_list_scores)[user.question_position];
        
        user.question_position = user.question_position + 1
        
        body = "Ответьте на вопрос:\n\n"+q_text
        
        #print(user.question_list_ansewers.items())
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Да")
        button_2 = types.KeyboardButton(text="Нет")
        button_back = types.KeyboardButton(text="Назад")
            
        keyboard_.add(button_1, button_2)
            
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
        bot.register_next_step_handler(message, process_question_from_file_step)
    else:
        q_to_update_key = list(user.question_list_scores)
        
        user.question_list_ansewers.update({q_to_update_key[user.question_position-1]:message.text})
        
        #print(user.question_list_ansewers.items())
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Дальше")
        button_back = types.KeyboardButton(text="Назад")
            
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text="Комментарий\n\nЕсли у вас возникли трудности с определением сложности декларации напишите про них тут или нажмите Дальше", reply_markup=keyboard_)
        bot.register_next_step_handler(message, process_commentary_step)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    pass;
    
@bot.message_handler(func=lambda message: True)
def check_text(message):
    if message.text.find("/start")>=0 or message.text.find("Назад")>=0:
        body = "Здравствуйте! Я официальный бот компании Nalog.nl B. V. У меня вы можете заказать налоговую декларацию 2017"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Заказать годовую декларацию 2017")
        
        keyboard_.add(button_1)
        
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)
    elif message.text.find("Заказать годовую декларацию 2017")>=0:
        body = "Вам необходимо выбрать форму.\n\n    1)Для частных лиц, весь отчетный год прописанных в НЛ (Форма Р)\n    2)Для частных лиц, часть отчетного года прописанных в НЛ (Форма М)\n    3)Для частных лиц, весь отчетный год прописанных за рубежом НЛ (Форма С)"
        
        keyboard_ = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        button_1 = types.KeyboardButton(text="1")
        button_2 = types.KeyboardButton(text="2")
        button_3 = types.KeyboardButton(text="3")
        button_back = types.KeyboardButton(text="Назад")
        
        keyboard_.add(button_1, button_2, button_3)
        
        bot.register_next_step_handler(message, process_form_step)
        bot.send_message(chat_id=message.chat.id, text=body, reply_markup=keyboard_)

def telegram_main(n):
    bot.skip_pending = True
    try:
        bot.polling(none_stop=True,timeout=180)
    except:
        traceback_error_string=traceback.format_exc()
        with open("Error.Log", "a") as myfile:
            myfile.write("\r\n\r\n" + time.strftime("%c")+"\r\n<<error polling="">>\r\n"+ traceback_error_string + "\r\n<<error polling="">>")
        bot.stop_polling()
        time.sleep(10)

if __name__ == '__main__':
    telegram_main(1);
