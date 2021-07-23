import redis
from util import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

"""
Structure:
chat: the chat where the jio is created
jio_name: the title of the jio
user: the person who join the jio
orders: the line to be displayed (item + name + (paid))
=========
Workflow:
Start a jio -> Join jio (CRUD) -> Finalise jio -> Pay -> End jio
========
Tables:
meta [hmset]
- {'meta' + chat_id} -> 
    {'message_id' -> {message_id}
     'finalised'  -> {0 or 1}        # 0 for Flase, 1 for True
     'title' -> {jio_title}} 

item [hmset]
- {'item' + chat_id} -> 
    {{'u'+user_id} -> {order_item_string}}

"""

r = redis.Redis(host='localhost', decode_responses=True, port=6379)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi! To start a jio, type '/start_jio'")


def start_jio(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)

    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To start a jio, type '/start_jio <title>'")
    else:
        chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
            chat_id, user_id)

        # Send jio start message
        jio_name = ' '.join(arguments)
        reply = get_open_jio_name_string(jio_name)
        message = context.bot.send_message(chat_id, text=reply,
                                           parse_mode='html')

        # Initialise jio name and meta values
        metadata = {'title': jio_name,
                    'message_id': message.message_id, 'finalised': 0}
        r.hmset(chat_id_meta_string, metadata)

        # Delete any existing jio in the group chat
        r.delete(chat_id_item_string)


def edit_jio_info(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)

    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To edit a jio, type '/edit_jio <new_jio_info>'")
    else:
        chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
            chat_id, user_id)

        # Get updated jio title
        jio_name = ' '.join(arguments)
        message_id = int(r.hget(chat_id_meta_string, 'message_id'))

        # Change jio name and meta values
        metadata = r.hgetall(chat_id_meta_string)
        metadata['title'] = jio_name
        r.hmset(chat_id_meta_string, metadata)

        # Form updated message
        orders = r.hgetall(chat_id_item_string)
        orders_string = '\n'.join(['%s' % value for value in orders.values()])
        reply = get_open_jio_name_string(jio_name) + orders_string

        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=reply, parse_mode='html')


def join_jio(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return

    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To add an item to this jio, type '/join_jio <item>'")
    else:
        chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
            chat_id, user_id)

        message_id = int(r.hget(chat_id_meta_string, 'message_id'))
        order_message = ' '.join(arguments) + ' ' + user_name

        orders = r.hgetall(chat_id_item_string)
        # Do nothing if updated item is the same as initial item
        if user_id_string in orders and order_message == orders[user_id_string]:
            return

        # Update item
        orders[user_id_string] = order_message
        r.hmset(chat_id_item_string, orders)

        # Form update message
        updated_orders = '\n'.join(['%s' % value for value in orders.values()])
        jio_name = r.hget(chat_id_meta_string, 'title')
        reply = get_open_jio_name_string(jio_name) + updated_orders

        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=reply, parse_mode='html')


def quit_jio(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)

    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
        chat_id, user_id)

    orders = r.hgetall(chat_id_item_string)
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    if user_id_string not in orders:
        context.bot.send_message(chat_id=chat_id,
                                 text="Sorry, you are not in the current jio. x(")
    else:
        original_message = orders[user_id_string]

        if finalised:
            context.bot.send_message(chat_id=chat_id,
                                     text="You cannot quit a jio after it is finalised.")
        else:
            del orders[user_id_string]
            r.hdel(chat_id_item_string, user_id_string)

            # Form edited message
            jio_name = r.hget(chat_id_meta_string, 'title')
            updated_orders = '\n'.join(
                ['%s' % value for value in orders.values()])
            reply = get_open_jio_name_string(jio_name) + updated_orders

            context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=reply, parse_mode='html')


def paid(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)

    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
        chat_id, user_id)

    orders = r.hgetall(chat_id_item_string)
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    if user_id_string not in orders:
        context.bot.send_message(chat_id=chat_id,
                                 text="Sorry, you are not in the current jio. x(")
    elif finalised == 0:
        context.bot.send_message(chat_id=chat_id,
                                 text="Wait a bit for the jio to be finalised.")
    else:
        original_message = orders[user_id_string]

        # Mark as paid if user has not paid.
        order_message = original_message
        if '✅' not in order_message:
            order_message = original_message + ' ✅'

        orders[user_id_string] = order_message
        r.hmset(chat_id_item_string, orders)

        jio_name = r.hget(chat_id_meta_string, 'title')

        updated_orders = '\n'.join(['%s' % value for value in orders.values()])

        reply = get_open_jio_name_string(jio_name) + updated_orders

        context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=reply, parse_mode='html')

        # Check if everyone paid, if so, end the jio.
        everyone_paid = True
        for order in updated_orders:
            if '✅' not in order_message:
                everyone_paid = False

        if everyone_paid:
            r.delete(chat_id_meta_string)
            r.delete(chat_id_item_string)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Everyone paid! Jio session ended.")


def end_jio(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
        chat_id, user_id)
    jio_name = r.hget(chat_id_meta_string, 'title')

    if r.get(chat_id):
        r.delete(chat_id)
        r.delete(chat_id_string)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Your current jio '" + jio_name + "' is terminated. See you next time!")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="There is no ongoing jio, use '/start_jio <jio_description>' to start a jio!")


def finalise_jio(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
        chat_id, user_id)

    orders = r.hgetall(chat_id_item_string)
    metadata = r.hgetall(chat_id_meta_string)
    metadata['finalised'] = 1
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    jio_name = r.hget(chat_id_meta_string, 'title')
    orders = '\n'.join(['%s' % value for value in orders.values()])
    reply = get_finalised_jio_name_string(jio_name) + orders
    message = context.bot.send_message(chat_id, text=reply, parse_mode='html')

    # Update message_id to the finalised message
    r.set(chat_id, message.message_id)


def send_pm(update, context):
    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(
        chat_id, user_id)

    context.bot.send_message(
        chat_id=user_id, text="Hi, you joined xxx jio session.")
