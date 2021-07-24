from functions import *
import os
import redis

# r = redis.Redis(host='localhost', port=6379)

import logging
import requests

from telegram.ext import MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext

bot_token = "1843778002:AAFxOoXX7xWTubiMmULqkTlQ9U0267zHa4I"
PORT = int(os.environ.get('PORT', 5000))

# Setting up our logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def main():
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
    
    # Setting up their polling stuff
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Create and add command handlers
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    start_jio_handler = CommandHandler('start_jio', start_jio)
    dispatcher.add_handler(start_jio_handler)

    edit_jio_title_handler = CommandHandler('edit_jio_title', edit_jio_title)
    dispatcher.add_handler(edit_jio_title_handler)

    join_jio_handler = CommandHandler("join_jio", join_jio)
    dispatcher.add_handler(join_jio_handler)

    finalise_jio_handler = CommandHandler('finalise_jio', finalise_jio)
    dispatcher.add_handler(finalise_jio_handler)

    paid_handler = CommandHandler("paid", paid)
    dispatcher.add_handler(paid_handler)

    end_jio_handler = CommandHandler('end_jio', end_jio)
    dispatcher.add_handler(end_jio_handler)

    quit_jio_handler = CommandHandler('quit_jio', quit_jio)
    dispatcher.add_handler(quit_jio_handler)

    confirm_finalise_handler = CallbackQueryHandler(callback = confirm_finalise_jio, pattern = r'confirm_finalise' )
    dispatcher.add_handler(confirm_finalise_handler)

    cancel_handler = CallbackQueryHandler(callback = cancel, pattern = r'cancel' )
    dispatcher.add_handler(cancel_handler)


    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                        port=int(PORT),
                        url_path=bot_token)

    updater.bot.setWebhook('https://floating-thicket-85827.herokuapp.com/' + bot_token)

    updater.idle() 

if __name__ == '__main__':
    main()