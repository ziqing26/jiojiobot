from telegram.ext import Updater, CallbackQueryHandler, CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import requests
import logging
from functions import *

# from functions import start, start_jio, end_jio, finalise_jio, join_jio, paid, send_pm, echo, caps
# Set your bot_token here
# (the same one as you've created and used just now!)
import redis
r = redis.Redis(host='localhost', port=6379)
# r.set("Hey Key", "Hey Value")
# test_key = r.get("Hey Key")
# print(test_key)


bot_token = "1843778002:AAFxOoXX7xWTubiMmULqkTlQ9U0267zHa4I"

# Importing python-telegram-bot's library functions

# Setting up our logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Setting up their polling stuff
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

# Create and add command handlers
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

start_jio_handler = CommandHandler('start_jio', start_jio)
dispatcher.add_handler(start_jio_handler)

edit_jio_info_handler = CommandHandler('edit_jio_info', start_jio)
dispatcher.add_handler(edit_jio_info_handler)

end_jio_handler = CommandHandler('end_jio', end_jio)
dispatcher.add_handler(end_jio_handler)

finalise_jio_handler = CommandHandler('finalise_jio', finalise_jio)
dispatcher.add_handler(finalise_jio_handler)

join_jio_handler = CommandHandler("join_jio", join_jio)
dispatcher.add_handler(join_jio_handler)

paid_handler = CommandHandler("paid", paid)
dispatcher.add_handler(paid_handler)

echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)

caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

callback_handler = CallbackQueryHandler(callback=send_pm, pattern=r'\w*')
dispatcher.add_handler(callback_handler)

# updater.start_polling()

# # Start the Bot
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=bot_token)
updater.bot.setWebhook(
    'https://floating-thicket-85827.herokuapp.com/' + bot_token)

updater.idle()
