from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import zipfile
from PIL import Image
import requests
import re
import os
import uuid
import errno

TOKEN = "xxx"
PATH_DIRECTORY = "temp"

logging.basicConfig(format='%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def start(bot, update):
    reply_keyboard = [['Batch mode: ON'],['Settings'],['Help','Rate','About']]
    update.message.reply_text('''Welcome! send me any sticker or sticker pack link, example http://t.me/addstickers/animals''', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False))

def help(bot, update):
    update.message.reply_text('''✅How to save sticker ?
tap on the sticker file sent by bot and then save to gallery.
-------
✅What is Batch mode?
Batch mode is saving some bunch of stickers in one zip file.
-------
Send Link of Sticker Pack The Bot will send you all stickers of the Pack as Zip.

✅How to get Link of a Sticker Pack?
You can Find Sticker Pack Link in 

Settings > Stickers & Masks > Click on 3 Dots next to sticker Pack > Share The Sticker Pack 
-------
for support, read channel about section.''')

def echo(bot, update):
    if update.message.text == "About":
        update.message.reply_text("""This bot was created with intention to help Telegram users download any telegram stickers that can be used in other messengers like whatsapp,facebook etc .""")
    elif update.message.text == "Settings":
        update.message.reply_text("...") #TODO
    elif update.message.text == "Help":
        update.message.reply_text("""✅How to save sticker ?
tap on the sticker file sent by bot and then save to gallery.
-------
✅What is Batch mode?
Batch mode is saving some bunch of stickers in one zip file.
-------
Send Link of Sticker Pack The Bot will send you all stickers of the Pack as Zip.

✅How to get Link of a Sticker Pack?
You can Find Sticker Pack Link in 

Settings > Stickers & Masks > Click on 3 Dots next to sticker Pack > Share The Sticker Pack.""")
    elif update.message.text == "Rate":
        update.message.reply_text("""If you like me, please give 5 star ⭐️⭐️⭐️⭐️⭐️ rating at: https://telegram.me/storebot?start=xyz 
 You can also recommend me to your friends. 
Have a nice day!""")
    elif update.message.text == "Batch mode: ON":
        update.message.reply_text("""batch mode enabled.Now send me stickers as much as you want,when you want to finish select Batch mode: OFF from keyboard.""")
    elif update.message.text == "Batch mode: OFF":
        update.message.reply_text("batch mode disabled.")
    else:
        set_name = (update.message.text).split('/')[-1]
        zip_filename = "{}.zip".format(set_name+"_webp")
        update.message.reply_text("You will soon receive a zip file containing all of the stickers in this pack.")    
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
          for sticker in bot.getStickerSet(set_name).stickers:

            file_name = "%s.webp" % (sticker.file_id)
            new_file = bot.getFile(sticker.file_id)
            new_file.download(file_name)
            zipf.write(file_name)
            os.remove(file_name)

        with open(zip_filename, 'rb') as f:
          update.message.reply_document(f, reply_to_message_id=update.message.message_id)
        os.remove(zip_filename)

def download_sticker(stickerId):
    url = 'https://api.telegram.org/bot{}/getFile?file_id={}'.format(TOKEN, stickerId)
    r = requests.get(url)
    if r.status_code != 200:
        return {'success': False, 'msg': 'Connection error'}
    data = r.json()
    if data['ok']:
        url = 'https://api.telegram.org/file/bot{}/{}'.format(TOKEN, data['result']['file_path'])
        response = requests.get(url)
        if response.status_code == 200:
            path = PATH_DIRECTORY + '/' +uuid.uuid4().hex[0:8]+'.webp'
            with open(path, 'wb') as f:
                f.write(response.content)
        return {'success': True, 'msg': 'OK', 'path': path}

def convert_png(path):
    im = Image.open(path)
    im.load()
    alpha = im.split()[-1]
    im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
    mask = Image.eval(alpha, lambda a: 255 if a <=128 else 0)
    im.paste(255, mask)
    newPath = path.replace(".webp",".png")
    im.save(newPath, transparency=255)    
    return newPath

def stickers(bot, update):
    with open('random','w+') as opened:
        opened.write(str(update.message))
    result = download_sticker(update.message.sticker.file_id)
    if result['success']:
        image = convert_png(result['path'])
        bot.send_document(chat_id=update.message.chat.id, document=open(image, 'rb'), reply_to_message_id=update.message.message_id, caption="http://t.me/addstickers/{}".format(update.message.sticker.set_name))
        bot.send_photo(chat_id=update.message.chat.id, photo=open(image, 'rb'), reply_to_message_id=update.message.message_id, caption="http://t.me/addstickers/{}".format(update.message.sticker.set_name))
        with zipfile.ZipFile(PATH_DIRECTORY + '/webp_{}.zip'.format(update.message.sticker.set_name), 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(result['path'])
        zip = PATH_DIRECTORY + '/webp_{}.zip'.format(update.message.sticker.set_name)
        bot.send_document(chat_id=update.message.chat.id, document=open(zip, 'rb'), reply_to_message_id=update.message.message_id, caption="http://t.me/addstickers/{}".format(update.message.sticker.set_name))
        os.remove(result['path'])
        path = result['path']
        newPath = path.replace(".webp",".png")
        os.remove(newPath)
        os.remove(zip)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    try:
        os.makedirs(PATH_DIRECTORY)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.sticker, stickers))
    dp.add_error_handler(error)
    updater.start_polling(timeout=99999)
    print("Ready to rock..!")
    updater.idle()
if __name__ == '__main__':
    main()
