#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import django
import datetime as dt
os.environ["DJANGO_SETTINGS_MODULE"] = 'tour.settings'
django.setup()
from django.urls import reverse

from main.models import Tour
from logbuch.models import Logbucheintrag
from telebot.models import User
from bilder.models import Bild
from karte.models import Schlafplatz

import logging
import telegram  # pkg: python-telegram-bot
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import InlineQueryHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler, MessageHandler, Filters, RegexHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup



# ----- SETUP ------ #
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
updater = Updater(token='498664396:AAGcMqVSxVvnqxgC_a0twCnuIclORUEHYgI')
dispatcher = updater.dispatcher

# ----- Some statics ------ #
msg_greets= "*Hi* {},\n Gut dass du fragst, "
msg_start = "*Benutze mich!* \n Bin zwar noch in arbeit, aber trotzdem cool. \n Mit /menu kriegst du ne kleine 'grafische' Oberfläche. Mit /status behälst du immer im Blick, auf welcher Tour und an welchem Tag du dich gerade befindest.\nDu kannst mir direkt mehrere Foto oder einen Standort pro Tag schicken. Außerdem kannst du mir nen Text schicken, wenn #log darin vorkommt, werde ich daraus ein Logbucheintrag erstellen, oder den Text an einen bestehenden Beitrag anhängen. Um die Strecke, Fahrzeit oder Höhenmeter anzugeben, benutze die entsprechenden Befehle. In jedemfall solltest du vor jedem Eintrag darauf achten, dass der richtige Tag ausgewählt ist.\nÜber das Menu können unter Logbuch->Neuer Eintrag alle Daten für einen vollständigen Logbuch eintrag auf einmal eingegeben werden.\nDie Daten sind sobald ich geantwortet habe auf der Website unter https://tour.sarbot.de zu erreichen.\n\n*Befehle:*\n/start - zeigt diese Nachricht\n/status - generelle infos oder spzifisch mit param tour oder tag\n/menu - 'grafisches' Menu\n/tag <int> - zu Tag <int> springen, wenn kein parameter, wird versucht aus dem Startdatum der aktuelle Tag zu bestimmen\n /tour <str> - zu tour <str> Springen, öffnet Menu, wenn kein parameter\n/abbrechen - Bricht die aktuelle Konversation ab\n"



# ------- states ----------- #
EINTRAG_INIT = 0
EINTRAG_TAG = 1
EINTRAG_STRECKE = 2
EINTRAG_HOEHE = 3
EINTRAG_ZEIT = 4
EINTRAG_ORT = 5
EINTRAG_FOTO = 6
EINTRAG_TEXT = 7
EINTRAG_FERTIG = 8

# --------- Helper Functions -------- #
def get_or_create_user(update):
    """
    Diese Funktion durchsucht die Datenbank nach einem user mit passender
    chat_id, wenn keiner gefunden wurde, wird ein neuer erstellt in die DB
    geschrieben und übergeben.
    :param update: Nimmt ein telegram update objekt (für id und name)
    :return user: User-Objekt das aus der Datenbank erstellt wurde
    """
    try:
        chat_id = update.message.chat_id
    except:
        chat_id = update.callback_query.from_user.id

    user, new = User.objects.get_or_create(telegram_id=chat_id)

    return user, new


def unsup_type(bot, update):
    """not handled by any handler answer warning"""
    update.message.reply_text('Mit dem Format deiner Nachricht kann ich nichts anfangen.\nBisher habe ich nur gelernt mit Dateien, Locations und Text umzugehen. Die möglichen Befehle kannst du dir mit /start anzeigen lassen.')


def save_file(bot, update):
    """Triggered on incomming files of type document"""
    iod = False
    ion = False
    user, neu = get_or_create_user(update)
    try:
        eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
    except:
        pass
    path = 'media/upload'
    file_id = update.message.document.file_id
    name = update.message.document.file_name
    try:
        f_path = os.path.join(path, user.tour.alias)
    except:
        f_path = os.path.join(path, 'unknown')
    if not os.path.exists(f_path):
        os.makedirs(f_path)  # TODO: does this work rekursive?
    file_path = os.path.join(f_path, 'telegram_' + name)
    print('file incomming')
    print(update.message.document.mime_type[:5])
    if update.message.document.mime_type[:5] == 'image':
        print('image detected')
        # todo: check for images with this fname first
        bild = Bild()
        bild.bild = file_path
        try:
            bild.tour = user.tour
            bild.tagebucheintrag = eintrag
        except:
            pass
        bild.save()
        print('saved in Image db')

    file = bot.get_file(file_id)
    file.download(file_path)
    print('saved')


def add_location(bot, update):
    # adds location to database (Schlafplatz)
    user, new = get_or_create_user(update)
    log, new = Logbucheintrag.objects.get_or_create(tag=user.tag, tour=user.tour)
    loc = update.message.location
    geom = {'type': 'Point', 'coordinates': [loc.longitude, loc.latitude]}
    log.ort = geom
    log.save()
    if not new:
        update.message.reply_text('Position für Tag {} aktualisiert...'.format(user.tag))
    else:
        update.message.reply_text('Neue Position für Tag {} erfasst...'.format(user.tag))


# ------ Create Handle Functions ----- #

def start(bot, update):
    """ This Function is called on /start.
    Its telegrams style guide to serve some info and hints on this command
    """
    user, new = get_or_create_user(update)
    msg = msg_start
    if new:
        msg = msg_greets + msg_start

    bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode='Markdown')


def status(bot, update, args):
    """ Returns current user status variables...
    Usefull to see what day and tour is selected without clicking the menu
    todo: args for details like 'tour', 'logbuch', 'log', 'ort', 'bild'
    """
    user, new = get_or_create_user(update)
    try:
        tourname = str(user.tour)
    except:
        tourname = 'Keine Tour gefunden'
    try:
        tag = str(user.tag)
    except:
        tag = 'Kein Tag aktiv'
    if user.admin:
        admin = 'Ja'
    else:
        admin = 'Nein'
    seit = dt.datetime.strftime(user.created, '%d.%m.%y')
    status = '*Aktuelle Einstellungen:*\n\n'
    status += '*Tour:* {}\n'.format(tourname)
    status += '*Tag:* {}\n'.format(tag)
    status += '*Id:* {}\n'.format(user.telegram_id)
    status += '*Admin:* {}\n'.format(admin)
    status += '*Seit:* {}\n'.format(seit)
    bot.send_message(chat_id=user.telegram_id, text=status, parse_mode='Markdown')


def tag(bot, update, args):
    try:
        tag = int(args[0])
    except:
        update.message.reply_text('Das ist leider keine ganze Zahl: {}'.format(args[0]))
    user, neu = get_or_create_user(update)
    user.tag = tag
    user.save()
    update.message.reply_text('Du befindest dich jetzt in Tag {}'.format(tag))


def today(bot, update, args):
    user, neu = get_or_create_user(update)
    try:
        start = user.tour.date_start
    except:
        update.reply_text('Sicher, dass die Tour ausgewählt und ein Startdatum angegeben ist? Prüfe mit /status und /status tour')


def parse_text(bot, update):
    text = update.message.text
    if '#log' in text:
        update.message.text.replace('#log', '')
        append_or_create_log(bot, update)


def append_or_create_log(bot, update):
    # triggered by #log
    user, new = get_or_create_user(update)
    try:
        eintrag, log_neu = Logbucheintrag.objects.get_or_create(tour=user.tour, tag=user.tag)
        if log_neu:
            update.message.reply_text('Neuen Eintrag für Tag {} erstellt'.format(user.tag))
        else:
            update.message.reply_text('An Tag {} angehängt.'.format(user.tag))
    except:
        update.message.reply_text('Das hat nicht geklappt. Ist der Tag und die Tour ausgewählt? /status /tag /today')


# ------------------ Create UI Functions ------------------------------------- #

def ui(bot, update):
    user, new = get_or_create_user(update)
    """
    if user.tour:
        ui_tour(bot, update)
    """

    msg = 'Wähle eine der folgenden Touren:'
    touren = Tour.objects.all()
    keyboard = []
    for tour in touren:
        try:
            btn = InlineKeyboardButton(tour.name,
                                       callback_data='ui_tour;{}'.format(tour.alias)),
            keyboard.append([*btn])
        except:
            print('error')
            logging.exception('Could not create Button for Tourlist')

    keyboard.append([InlineKeyboardButton('Neu erstellen', callback_data='ui_new;')])
    markup = InlineKeyboardMarkup(keyboard)
    try:  # to get a messg_id and edit
        print('trying')
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(
            text=msg,
            chat_id=user.telegram_id,
            message_id=msg_id,
            parse_mode='Markdown',
            reply_markup=markup)
        print('done')
    except:  # create new
        print('exception')
        print(user.telegram_id)
        bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode='Markdown', reply_markup=markup)
        print('msg send')


def ui_tour(bot, update):

    # create default keyboard (main menu)
    user, new = get_or_create_user(update)
    msg = 'Ausgewählte Tour: {}'.format(user.tour.name)
    keyboard = [[
        InlineKeyboardButton('Tour bearbeiten', callback_data='ui_tour_edit')],[
        InlineKeyboardButton('Tour wechseln', callback_data='ui_tour_change')],[
        InlineKeyboardButton('Logbuch', callback_data='ui_tour_logbuch')],[
        InlineKeyboardButton('Bilder', callback_data='ui_tour_bilder')],[
        InlineKeyboardButton('Abbrechen',
                             callback_data='cfg_cancel')
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    try:  # to get a messg_id
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(
            text=msg,
            chat_id=user.telegram_id,
            message_id=msg_id,
            parse_mode='Markdown',
            reply_markup=markup)
    except:  # create new
        bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode='Markdown', reply_markup=markup)


def ui_tour_logbuch(bot, update):
    user, new = get_or_create_user(update)
    try:
        msg = 'Logbucheinträge für {}'.format(user.tour.name)
    except:
        print('no tour name')
        msg = 'Logbucheinträge für {}'.format(user.tour.alias)

    eintraege = Logbucheintrag.objects.filter(tour=user.tour)
    keyboard = []
    for eintrag in eintraege:
        try:
            btn = InlineKeyboardButton('Tag {}'.format(eintrag.tag),
                                       callback_data='ui_tour_logbucheintrag;{}'.format(eintrag.tag)),
            keyboard.append([*btn])
        except:
            print('error')
            logging.exception('Could not create Button for Eintragslist')
    keyboard.append([InlineKeyboardButton('Neu erstellen', callback_data='ui_tour_logbuch_neu;')])
    markup = InlineKeyboardMarkup(keyboard)
    try:  # to get a messg_id
        msg_id = update.callback_query.message.message_id
        bot.edit_message_text(
            text=msg,
            chat_id=user.telegram_id,
            message_id=msg_id,
            parse_mode='Markdown',
            reply_markup=markup)
    except:  # create new
        bot.send_message(chat_id=user.telegram_id, text=msg,
                         parse_mode='Markdown', reply_markup=markup)


def ui_tour_logbuch_neu(bot, update):
    user, new = get_or_create_user(update)
    try:
        msg = 'Neuer Eintrag für {}'.format(user.tour.name)
    except:
        bot.send_message(chat_id=user.telegram_id, text='WARNUNG: Tour hat keinen Namen')
        msg = 'Neuer Eintrag für {}'.format(user.tour.alias)
    msg += '\n Mit /skip kannst du die Frage überspringen und mit /abbrechen die Konversation abbrechen.'
    msg += '\n Für den wievielten TAG der Tour soll der neue Eintrag sein? \nBitte nur die Zahl angeben.'
    bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode='Markdown')
    return EINTRAG_TAG



# ---------- logbuch conversation handler ------------- #
def logbuch_tag(bot, update):
    user, new = get_or_create_user(update)
    try:
        print('Antwort TAG: {}'.format(update.message.text))  # TODO: logging
        user.tag = int(update.message.text)  # um fuer weitere abfragen zu merken
        user.save()
        # neuen eintrag erstellen
        # TODO: ausschließen das eintrag nicht existiert, ansonsten auf edit umleiten
        eintrag = Logbucheintrag(tag=user.tag)
        #todo tour setzen:
        eintrag.tour = user.tour #testen
        eintrag.save()
        bot.send_message(chat_id=user.telegram_id, text='Hab nen Eintrag für Tag {} erstellt. \n Jetzt die Strecke in KM'.format(update.message.text))
        return EINTRAG_STRECKE
    except Exception as e:
        bot.send_message(chat_id=user.telegram_id, text='Da ging was schief, versuchs nochmal...\n{}'.format(e))
        return EINTRAG_TAG


def logbuch_strecke(bot, update):
    user, new = get_or_create_user(update)
    try:
        strecke = float(update.message.text)
        eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
        eintrag.strecke = strecke
        eintrag.save()
        print('Antwort STRECKE: {}'.format(strecke))
        bot.send_message(chat_id=user.telegram_id, text='Danke, jetzt die Hoehenmeter...')
        return EINTRAG_HOEHE
    except Exception as e:
        print('eintrag nicht gefunden oder konnte strecke nicht eintragen..')
        bot.send_message(chat_id=user.telegram_id, text='Ups, das hat nicht geklappt:\n{}'.format(e))
        return EINTRAG_STRECKE


def logbuch_hoehe(bot, update):
    user, new = get_or_create_user(update)
    try:
        hoehe = float(update.message.text)
        eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
        eintrag.hoehe = hoehe
        eintrag.save()
        bot.send_message(chat_id=user.telegram_id, text='Ist notiert, jetzt die Zeit in Stunden.')
        return EINTRAG_ZEIT
    except Exception as e:
        bot.send_message(chat_id=user.telegram_id, text='Ups, da hat was nicht geklappt...\n{}'.format(e))
        return EINTRAG_HOEHE


def logbuch_zeit(bot, update):
    user, new = get_or_create_user(update)
    try:
        zeit = float(update.message.text)
        eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
        eintrag.uptime = zeit
        eintrag.save()
        bot.send_message(chat_id=user.telegram_id, text='Ok Super.. weiter gehts mit dem Schlafplatz, schick mir den Standort.')
        return EINTRAG_ORT
    except Exception as e:
        bot.send_message(chat_id=user.telegram_id, text='Nope.. Fehler, denk dran, zahlen mit . statt ,\n{}'.format(e))
        return EINTRAG_ZEIT


def logbuch_ort(bot,update):
    user, new = get_or_create_user(update)
    try:
        ort = update.message.location
        eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
        eintrag.lon = ort.longitude
        eintrag.lat = ort.latitude
        eintrag.save()
        geom = {'type': 'Point', 'coordinates': [ort.longitude, ort.latitude]}
        platz, platz_neu = Schlafplatz.objects.get_or_create(geom=geom, tour=user.tour, tag=user.tag)
        platz.save()
        if platz_neu:
            update.message.reply_text('Neuen Spot auf der Karte erstellt.')
        bot.send_message(chat_id=user.telegram_id, text='In der DB gespeichert.. Noch nen Foto vom Schlafplatz? (geht noch nicht)')
        return EINTRAG_FOTO
    except Exception as e:
        bot.send_message(chat_id=user.telegram_id, text='Nope.. war das nen Standort? Machen wir später, versuchs mit nem Foto... (noch in arbeit) \n{}'.format(e))
        return EINTRAG_FOTO


def logbuch_foto(bot,update):
    user, new = get_or_create_user(update)
    bot.send_message(chat_id=user.telegram_id, text='sorry das speichern des Fotos funktioniert noch nicht :(, aber text sollte gehen. Schreib mir was heute passiert ist.')
    return EINTRAG_TEXT

def logbuch_text(bot,update):
    user, new = get_or_create_user(update)
    text = update.message.text
    eintrag = Logbucheintrag.objects.get(tag=user.tag, tour=user.tour)
    eintrag.text = text
    eintrag.save()
    bot.send_message(chat_id=user.telegram_id, text='Ok sollte jetzt alles eingetragen sein, schaue doch nochmal nach um sicher zu gehen..')
    return EINTRAG_FERTIG






# ------ Button definitions --------- #
def button_callback(bot, update):
    data = update.callback_query.data.split(';')
    user, new = get_or_create_user(update)
    if data[0] == 'ui_tour':
        try:
            print(data[1])
            user.tour = Tour.objects.get(alias=data[1])
            user.save()
            ui_tour(bot, update)
        except:
            print('error in callback')
    elif data[0] == 'ui_tour_edit':
        pass
    elif data[0] == 'ui_tour_change':
        ui(bot, update)
    elif data[0] == 'ui_tour_logbuch':
        print('logbuch')
        ui_tour_logbuch(bot, update)
    elif data[0] == 'ui_tour_logbuch_neu':
        #bot.send_message(chat_id=user.telegram_id, text='Wenn das Eintragen übers Menu nicht startet, benutze den /log Befehl um die Eingabe zu starten.')
        ui_tour_logbuch_neu(bot, update)
        return EINTRAG_TAG
    else:
        logging.warning('unbekannter button gedrückt')


#logging.warning(usr.chat_id, usr.first_name)


# ----- Regist Handler ----- #

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

status_handler = CommandHandler('status', status, pass_args=True)
dispatcher.add_handler(status_handler)

#select_tour_handler = CommandHandler('tour', select_tour)
#dispatcher.add_handler(select_tour_handler)

#select_tag_handler = CommandHandler('tag', select_tag)
#dispatcher.add_handler(select_tag_handler)



#logbuch_handler = CommandHandler('logbuch', ui_tour_logbuch)
#dispatcher.add_handler(logbuch_handler)

ui_handler = CommandHandler('menu', ui)
dispatcher.add_handler(ui_handler)

tag_handler = CommandHandler('tag', tag, pass_args=True)
dispatcher.add_handler(tag_handler)

neuer_eintrag_handler = CommandHandler('log', ui_tour_logbuch_neu)
#dispatcher.add_handler(neuer_eintrag_handler)

#https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py
callback_handler = CallbackQueryHandler(button_callback)
neuer_eintrag_conversation = ConversationHandler(entry_points=[ui_handler, neuer_eintrag_handler, callback_handler],
                                                 states={EINTRAG_TAG: [MessageHandler(Filters.text, logbuch_tag)],
                                                         EINTRAG_STRECKE: [MessageHandler(Filters.text, logbuch_strecke)],
                                                         EINTRAG_HOEHE: [MessageHandler(Filters.text, logbuch_hoehe)],
                                                         EINTRAG_ZEIT: [MessageHandler(Filters.text, logbuch_zeit)],
                                                         EINTRAG_ORT: [MessageHandler(Filters.location, logbuch_ort), MessageHandler(Filters.text, logbuch_ort)],
                                                         EINTRAG_FOTO: [MessageHandler(Filters.photo, logbuch_foto), MessageHandler(Filters.text, logbuch_foto)],
                                                         EINTRAG_TEXT: [MessageHandler(Filters.text, logbuch_text)],
                                                         },
                                                 fallbacks=[CommandHandler('abbrechen', logbuch_tag)])  #TODO: replace regex handler to parse int
dispatcher.add_handler(neuer_eintrag_conversation)
dispatcher.add_handler(callback_handler)

text_handler = MessageHandler(Filters.text, parse_text)
dispatcher.add_handler(text_handler)

file_handler = MessageHandler(Filters.document, save_file)
dispatcher.add_handler(file_handler)

location_handler = MessageHandler(Filters.location, add_location)
dispatcher.add_handler(location_handler)

other_handler = MessageHandler(Filters.all, unsup_type)
dispatcher.add_handler((other_handler))

"""
new_handler = CommandHandler('new', new, pass_args=True)
dispatcher.add_handler(new_handler)

map_handler = CommandHandler('map', locate, pass_args=True)
dispatcher.add_handler(map_handler)

help_handler = CommandHandler('help', help_text)
dispatcher.add_handler(help_handler)

show_handler = CommandHandler('show', show_event, pass_args=True)
dispatcher.add_handler(show_handler)

dispatcher.add_handler(CallbackQueryHandler(button))
"""

# ---- Start Bot ---- #
updater.start_polling()