import telebot
import requests
from googletrans import Translator
import json
import os
import difflib
import random

bot = telebot.TeleBot("<TOKEN>")
dir_path = r"D:\Programming\PycharmProjects\taxi-telegram-bot"
path_count = "count.json"
path_exclude = "exclude.json"
path_cuisine = "cuisines.json"
path_mealtype = "mealtype.json"

translator = Translator()

count_db = {}
exclude_db = {}
cuisine_db = {}
mealtype_db = {}
mealtypes = ['All', 'Breads', 'Breakfast', 'Cakes', 'Casseroles', 'Cookies', 'Desserts', 'Dinner', 'Dips', 'Drinks', 'Fish recipes', 'Grilling & BBQ', 'Kid Friendly', 'Meat recipes', 'Poutry recipes', 'Quick & Easy', 'Salad Dressings', 'Salads', 'Sandwiches', 'Sauses', 'Seafood recipies', 'Slow Cooker', 'Soups', 'Veggie recipes']
cuisines = ['All', 'Asian', 'Caribbean', 'Chinese', 'French', 'German', 'Indian & Thai', 'Italian', 'Mediterranean', 'Mexican', 'Tex-Mex & Southwest']

results_db = {}

def read_data(path):
    data = json.load(open(path))
    data = {int(k): v for k, v in data.items()}
    return data


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

if os.path.exists(os.path.join(dir_path, path_count)):
    count_db = read_data(path_count)
else:
    count_db = {}

if os.path.exists(os.path.join(dir_path, path_exclude)):
    exclude_db = read_data(path_exclude)
else:
    exclude_db = {}

if os.path.exists(os.path.join(dir_path, path_cuisine)):
    cuisine_db = read_data(path_exclude)
else:
    cuisine_db = {}

if os.path.exists(os.path.join(dir_path, path_mealtype)):
    mealtype_db = read_data(path_mealtype)
else:
    mealtype_db = {}

@bot.message_handler(commands=['cook'])
def check(message):
    ingridients = message.text[6:]
    ingridients = translator.translate(ingridients, dest='en').text
    ingridients = "".join(ingridients.split())
    if not message.chat.id in count_db:
        count_db[message.chat.id] = 5
        with open('count.json', 'w') as outfile:
            json.dump(count_db, outfile)
    if not message.chat.id in exclude_db:
        exclude_db[message.chat.id] = ""
        with open('exclude.json', 'w') as outfile:
            json.dump(exclude_db, outfile)
    catname = ""
    if message.chat.id in cuisine_db:
        catname = cuisine_db[message.chat.id]
    if message.chat.id in mealtype_db:
        if len(catname) > 0:
            catname = catname + ',' + mealtype_db[message.chat.id]
        else:
            catname = mealtype_db[message.chat.id]

    r = requests.post('http://www.supercook.com/dyn/results',
                      data={"needsimage": 1, "catname": catname, "kitchen": ingridients, "start": 0,
                            "exclude": exclude_db[message.chat.id]})
    text_dict = dict(json.loads(r.text))
    results = text_dict['results']
    total_can_make_right_now = text_dict["total_can_make_right_now"]
    results = results[:total_can_make_right_now]
    results_db[message.chat.id] = results
    random.shuffle(results)
    bot.send_message(message.chat.id, 'Total recipes found: ' + str(total_can_make_right_now))
    if total_can_make_right_now < count_db[message.chat.id]:
        count = total_can_make_right_now
    else:
        count = count_db[message.chat.id]

    if total_can_make_right_now > 0:
        for i in range(count):
            bot.send_message(message.chat.id, results[i]['title'] + "\n" + results[i]['url'])
            results_db[message.chat.id].pop(0)
        if len(results_db[message.chat.id]) > 0:
            if len(results_db[message.chat.id]) < count_db[message.chat.id]:
                bot.send_message(message.chat.id,
                                 'Show next ' + str(len(results_db[message.chat.id])) + ' results with /next')
            else:
                bot.send_message(message.chat.id, 'Show next ' + str(count_db[message.chat.id]) + ' results with /next')
    else:
        bot.send_message(message.chat.id, "Can't find any recepies with that")


@bot.message_handler(commands=['exclude'])
def exclude(message):
    excluding = message.text[9:]
    excluding = translator.translate(excluding, dest='en').text
    excluding = "".join(excluding.split())
    excluding = excluding.replace('vegan', 'poultry,meat,dairy,shellfish,fish,eggs,honey')
    excluding = excluding.replace('vegetarian', 'poultry,meat,fish,shellfish')
    excluding = excluding.replace('pestacatarian', 'poultry,meat')
    if len(excluding) > 0:
        exclude_db[message.message_id] = excluding
        bot.send_message(message.chat.id, 'Excludings updated')
    else:
        bot.send_message(message.chat.id, 'Wrong arguments')
    with open('exclude.json', 'w') as outfile:
        json.dump(exclude_db, outfile)


@bot.message_handler(commands=['count'])
def count(message):
    counting = message.text[7:]
    if RepresentsInt(counting):
        count_db[message.chat.id] = counting
        bot.send_message(message.chat.id, 'Count updated')
    else:
        bot.send_message(message.chat.id, 'Not a number')
    with open('count.json', 'w') as outfile:
        json.dump(count_db, outfile)


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(chat_id= message.chat.id,text = "/count - number of dishes you want(5 dishes is default)")
    bot.send_message(chat_id= message.chat.id,text =  "/exclude - write vegan, vegetarian or pescetarian to exclude some products")
    bot.send_message(chat_id= message.chat.id,text = "/cook ingradient,ingradient - show dishes")


@bot.message_handler(commands=['cuisine'])
def cuisine(message):
    cuisine_type = message.text[9:]
    cuisine_type = translator.translate(cuisine_type, dest='en').text
    cuisine_type = "".join(cuisine_type.split()).title()
    if cuisine_type in cuisines:
        if cuisine_type == 'All':
            cuisine_type = ""
        cuisine_db[message.chat.id] = cuisine_type
        with open('cuisines.json', 'w') as outfile:
            json.dump(cuisine_db, outfile)
        bot.send_message(message.chat.id, 'Cuisine changed')
    else:
        probable_type = difflib.get_close_matches(cuisine_type, cuisines, 1, 0.4)
        if len(probable_type) > 0:
            bot.send_message(message.chat.id, 'Maybe you meant "' + probable_type[0] + '"? Applying it.')
            cuisine_db[message.chat.id] = probable_type[0]
            with open('cuisines.json', 'w') as outfile:
                json.dump(cuisine_db, outfile)
        else:
            bot.send_message(message.chat.id, 'Can not find this cuisine. Use /cuisines to list all available')


@bot.message_handler(commands=['mealtype'])
def mealtype(message):
    meal_type = message.text[10:]
    meal_type = translator.translate(meal_type, dest='en').text
    meal_type = "".join(meal_type.split()).title()
    if meal_type in mealtypes:
        if meal_type == 'All':
            meal_type = ""
        mealtype_db[message.chat.id] = meal_type
        with open('mealtype.json', 'w') as outfile:
            json.dump(mealtype_db, outfile)
        bot.send_message(message.chat.id, 'Meal type changed')
    else:
        probable_type = difflib.get_close_matches(meal_type, mealtypes, 1, 0.4)
        if len(probable_type) > 0:
            bot.send_message(message.chat.id, 'Maybe you meant "' + probable_type[0] + '"? Applying it.')
            mealtype_db[message.chat.id] = probable_type[0]
            with open('mealtype.json', 'w') as outfile:
                json.dump(mealtype_db, outfile)
        else:
            bot.send_message(message.chat.id, 'Can nott find this meal type. Use /mealtypes to list all available')


@bot.message_handler(commands=['mealtypes'])
def mealtypes_list(message):
    bot.send_message(message.chat.id, ', '.join(mealtypes))


@bot.message_handler(commands=['cuisines'])
def cuisines_list(message):
    bot.send_message(message.chat.id, ', '.join(cuisines))


@bot.message_handler(commands=['listsettings'])
def settings_list(message):
    settingslist = "Your settings:\n"
    if message.chat.id in count_db:
        settingslist += '    Count: ' + str(count_db[message.chat.id]) + '\n'
    else:
        settingslist += '    Count: 5\n'
    if message.chat.id in exclude_db:
        settingslist += '    Excluded ingridients: ' + exclude_db[message.chat.id] + '\n'
    else:
        settingslist += '    Excluded ingridients: none\n'
    if message.chat.id in cuisine_db:
        settingslist += '    Cuisine: ' + cuisine_db[message.chat.id] + '\n'
    else:
        settingslist += '    Cuisine: all\n'
    if message.chat.id in mealtype_db:
        settingslist += '    Meal type: ' + mealtype_db[message.chat.id] + '\n'
    else:
        settingslist += '    Meal type: all\n'

    bot.send_message(message.chat.id, settingslist)


@bot.message_handler(commands=['next'])
def shownext(message):
    if message.chat.id in results_db:
        if len(results_db[message.chat.id])>0:
            if len(results_db[message.chat.id]) < count_db[message.chat.id]:
                count = len(results_db[message.chat.id])
            else:
                count = count_db[message.chat.id]
            for i in range(count):
                bot.send_message(message.chat.id, results_db[message.chat.id][i]['title'] + "\n" + results_db[message.chat.id][i]['url'])
            for i in range(count):
                results_db[message.chat.id].pop(0)
            if len(results_db[message.chat.id])>0:
                if len(results_db[message.chat.id]) < count_db[message.chat.id]:
                   bot.send_message(message.chat.id, 'Show next ' + str(len(results_db[message.chat.id])) + ' results with /next')
                else:
                    bot.send_message(message.chat.id, 'Show next '+str(count_db[message.chat.id]) + ' results with /next')
        else:
            bot.send_message(message.chat.id, 'No recipes to show')
            del results_db[message.chat.id]
    else:
        bot.send_message(message.chat.id, 'You don`t have recipes to show')

bot.polling()




