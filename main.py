from logging import debug
import telebot
from requests import get
from telebot import types
from oauth2client.transport import request
import pandas as pd
import datetime
from datetime import date, timedelta
import httplib2
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from collections import defaultdict
from dateutil import relativedelta
import argparse
from oauth2client import client
from oauth2client import file
from oauth2client import tools
import re
import os
from urllib.parse import urlparse
import telebot
from telebot import types
import requests
import numpy as np
import math
import schedule
import time




from telegram.ext import Updater
from telegram.ext import CommandHandler
site_api = 'https://www.googleapis.com/webmasters/v3/sites'   
creds = 'client_secret_599934185146-vh3iul10m3et4njtkbt5p1r11clfct0n.apps.googleusercontent.com.json'        # Credential file from GSC
bot = telebot.TeleBot('2102986595:AAG5YH4NZDnhbGbx91IQjDVLCdJdqgTaoyg')



site_dict = {}
class Site:
    def __init__(self, domain):
        self.domain = domain
        self.needed_date = None
        self.url = None



def authorize_creds(creds):
    # Variable parameter that controls the set of resources that the access token permits.
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
 
    # Path to client_secrets.json file
    CLIENT_SECRETS_PATH = creds
 
    # Create a parser to be able to open browser for Authorization
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])
 
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope = SCOPES,
        message = tools.message_if_missing(CLIENT_SECRETS_PATH))
 
    # Prepare credentials and authorize HTTP
    # If they exist, get them from the storage object
    # credentials will get written back to a file.
    storage = file.Storage('authorizedcreds.dat')
    credentials = storage.get()
 
    # If authenticated credentials don't exist, open Browser to authenticate
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())
    webmasters_service = build('searchconsole', 'v1', http=http)
    return webmasters_service

def domains_founder(service, property_uri, request): 
    return service.sites().list().execute()

def execute_request(service, property_uri, request): 
    return service.searchanalytics().query(siteUrl=property_uri, body=request).execute()

webmasters_service = authorize_creds(creds)     # Get credentials to log in the api
request={
    'quotaUser':'string',
    'fields':'string',
    'upload_protocol':'string',
    'alt':'',
    'access_token':'string',
    'callback':'string',
    '$.xgafv':'',
    'uploadType':'string',
    'prettyPrint':'true'

}
response = domains_founder(webmasters_service, site_api, request)


@bot.message_handler(commands=['start'])
@bot.message_handler(regexp="Вернуться к старту")
def start(message):
    try:
        
        msg = bot.send_message(message.chat.id, 'Введите пароль')
        bot.register_next_step_handler(msg, check_password)
    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)


def check_password(message):
    try:
        if(message.text == "cat"):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            print(f" ID Пользователя : {message.from_user.id}")
            for val in response['siteEntry']:
                button = types.KeyboardButton(val['siteUrl'])
                markup.row(button)
            msg = bot.send_message(message.chat.id, 'It works!\n Выберите сайт, который вас интересует', reply_markup=markup)
        else:
            markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
            error_button = types.KeyboardButton("/start")
            markup_error_button.row(error_button)
            bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)
            msg = bot.send_message(message.chat.id, 'Не верный пароль вернитесь к старту', reply_markup=markup_error_button)
            bot.register_next_step_handler(msg, start)

    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)



@bot.message_handler(regexp="https://(\w+)[.](\w+)[/]$")
def choose_date(message):
    try:
        chat_id = message.chat.id

        domain = str(message.text)
        site=Site(domain)
        site_dict[chat_id] = site 
        print(f" ID Пользователя : {message.from_user.id}")
        msg = bot.reply_to(message, "Введите дату в виде: 2021-11-20\n Можно выбрать ток за 3 дня до сегодняшнего дня")
    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)


@bot.message_handler(regexp="\d\d\d\d-\d\d-\d\d")
def choose_url(message):
    try:
        
        chat_id = message.chat.id
        needed_date = message.text
        
        site = site_dict[chat_id]
        site.needed_date=needed_date
        keyboard = types.InlineKeyboardMarkup()
    

        webmasters_service = authorize_creds(creds)
        maxRows = 25000 # Maximum 25K per call 
        numRows = 0     # Start at Row Zero
        
        request = {
             "dataState": "ALL",
                    'startDate': site.needed_date,     # Get today's date (while loop)
                    'endDate': site.needed_date,       # Get today's date (while loop)
                    'dimensions': ['date','page','query'],  # Extract This information
                    'rowLimit': maxRows,                    # Set number of rows to extract at once (max 25k)
                    'startRow': numRows                     # Start at row 0, then row 25k, then row 50k... until with all.
                }

        
        response_messege = execute_request(webmasters_service, site.domain, request)
        #print(execute_request(webmasters_service, site.domain, request))


        array_of_url =[]
        for val in response_messege['rows']:
            array_of_url.append(val['keys'][1])
        array_of_url_unique = np.unique(array_of_url) 

        for elem in array_of_url_unique:
            key_url = types.InlineKeyboardButton(text=elem, callback_data=elem)
            keyboard.add(key_url)
            
            

    
        bot.reply_to(message, text='Выбери страницу', reply_markup=keyboard)
    
    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)


@bot.callback_query_handler(func=lambda call: True)

def show_style(call):

    chat_id = call.message.chat.id
    url=call.data
    site = site_dict[chat_id]
    site.url=url
    
    print(url)
    markup_choose = types.ReplyKeyboardMarkup(resize_keyboard=True)
    only_position = types.KeyboardButton("Показать только ключи и позиция")
    show_all =  types.KeyboardButton("Показать всю статистику")
    markup_choose.row(show_all, only_position)
    msg = bot.send_message(call.message.chat.id, "Как вывести список?", reply_markup=markup_choose)




    


@bot.message_handler(regexp="Показать всю статистику")
def show_all(message):
    try:
    
        markup_go_to_start =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        webmasters_service = authorize_creds(creds)
        maxRows = 25000 # Maximum 25K per call 
        numRows = 0     # Start at Row Zero
        chat_id = message.chat.id
        site = site_dict[chat_id]
        print(site.needed_date)
        print(site.needed_date)

        request = {
             "dataState": "ALL",
                'startDate': site.needed_date,     # Get today's date (while loop)
                'endDate': site.needed_date,       # Get today's date (while loop)
                'dimensions': ['date','page','query'],  # Extract This information
                'rowLimit': maxRows,                    # Set number of rows to extract at once (max 25k)
                'startRow': numRows                     # Start at row 0, then row 25k, then row 50k... until with all.
   }
            

            
        response_messege = execute_request(webmasters_service, site.domain, request)

        button = types.KeyboardButton("Вернуться к старту")
        markup_go_to_start.row(button)
        array_mesege =[]
        for val in response_messege['rows']:
            
            if site.url == val['keys'][1]: 
            # Формируем гороскоп
                print_messege = f"{val['keys'][2]} - clicks: {val['clicks']} - impressions: {val['impressions']} - position: {round(val['position'], 1)}"
                # Отправляем текст в Телеграм
                
                array_mesege.append(print_messege)

        #
        #print(len(array_mesege))
        counter = len(array_mesege) / 25
        #print(counter)
        number_of_rows_min=0 
        number_of_rows_max = 25
        i=0
        while (i<=math.ceil(counter)):
            #print(array_mesege[number_of_rows_min:number_of_rows_max])
            msg =bot.send_message(message.chat.id, '\n'.join(array_mesege[number_of_rows_min:number_of_rows_max]), reply_markup=markup_go_to_start)
            i = i +1 
            number_of_rows_max = number_of_rows_max + 25
            number_of_rows_min = number_of_rows_min +25
        bot.register_next_step_handler(msg, check_password)
            #print(len(response_messege['rows']))
        
   
        
    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)

@bot.message_handler(regexp="Показать только ключи и позиция")
def show_all(message):
    try:
    
        markup_go_to_start =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        webmasters_service = authorize_creds(creds)
        maxRows = 25000 # Maximum 25K per call 
        numRows = 0     # Start at Row Zero
        chat_id = message.chat.id
        site = site_dict[chat_id]
        print(site.needed_date)
        print(site.needed_date)

        request = {
                "dataState": "ALL",
                "startDate": site.needed_date,     # Get today's date (while loop)
                "endDate": site.needed_date,       # Get today's date (while loop)
                "dimensions": ['date','page','query'],  # Extract This information
                "rowLimit": maxRows,                    # Set number of rows to extract at once (max 25k)
                "startRow": numRows                     # Start at row 0, then row 25k, then row 50k... until with all.
            }

            
        response_messege = execute_request(webmasters_service, site.domain, request)

        button = types.KeyboardButton("Вернуться к старту")
        markup_go_to_start.row(button)
        array_mesege =[]
        for val in response_messege['rows']:
            
            if site.url == val['keys'][1]: 
            # Формируем гороскоп
                print_messege = f"{val['keys'][2]} {round(val['position'], 1)}"
                # Отправляем текст в Телеграм
                
                array_mesege.append(print_messege)

        #
        #print(len(array_mesege))
        counter = len(array_mesege) / 25
        #print(counter)
        number_of_rows_min=0 
        number_of_rows_max = 25
        i=0
        
        while (i<=math.ceil(counter)):
            #print(array_mesege[number_of_rows_min:number_of_rows_max])
            msg =bot.send_message(message.chat.id, '\n'.join(array_mesege[number_of_rows_min:number_of_rows_max]), reply_markup=markup_go_to_start)
            i = i +1 
            number_of_rows_max = number_of_rows_max + 25
            number_of_rows_min = number_of_rows_min +25
        bot.register_next_step_handler(msg, check_password)
            #print(len(response_messege['rows']))
        
   
        
    except:
        markup_error_button =  types.ReplyKeyboardMarkup(resize_keyboard=True)
        error_button = types.KeyboardButton("/start")
        markup_error_button.row(error_button)
        bot.send_message(message.chat.id, "Go to start", reply_markup=markup_error_button)
        





if __name__ == '__main__':


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
    bot.enable_save_next_step_handlers(delay=6)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
    bot.load_next_step_handlers()

    bot.polling(none_stop=True)
    