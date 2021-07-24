from util import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode 
import os
import redis

"""
Terminologies:
chat: the chat where the jio is created
jio: a collection of orders
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



def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi! To start a jio, type '/start_jio'")

# Create a new jio with a title
def start_jio(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)
    
    if r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="There is an ongoing jio. To end the jio, use '/end_jio'")
        return
    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To start a jio, type '/start_jio <title>'")
        return
    
    # Send jio start message
    jio_name = ' '.join(arguments)
    reply = get_open_jio_name_string(jio_name)
    message = context.bot.send_message(chat_id, text=reply, 
                parse_mode= 'html')
    
    # Initialise jio name and meta values
    metadata = {'title': jio_name, 'message_id': message.message_id, 'finalised': 0}
    r.hmset(chat_id_meta_string, metadata)
    
    # Delete any existing jio in the group chat
    r.delete(chat_id_item_string)
    
# Edit the title of the jio
def edit_jio_title(update, context): 
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return
    
    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To edit jio title, type '/edit_jio_title <new_jio_title>'")
    else:
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

        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply, parse_mode= 'html')

# Join a jio or update user's jio item      
def join_jio(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
    
    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)
    
    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return
    
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    if finalised == 1:
        context.bot.send_message(chat_id=chat_id,
                                 text="Current jio is finalised, join the next jio!")
    if not arguments:
        context.bot.send_message(chat_id=chat_id,
                                 text="To add an item to this jio, type '/join_jio <item>'")
    else:
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

        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply, parse_mode= 'html')

# Quit a joined jio before it is finalised
def quit_jio(update, context):   
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return

    orders = r.hgetall(chat_id_item_string)
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    if user_id_string not in orders:
        context.bot.send_message(chat_id=chat_id,
                                 text="Sorry, you are not in the current jio. 😢") 
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
            updated_orders = '\n'.join(['%s' % value for value in orders.values()])
            reply = get_open_jio_name_string(jio_name) + updated_orders

            context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply, parse_mode= 'html')

# Mark user's order as paid
def paid(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return

    orders = r.hgetall(chat_id_item_string)
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))
    finalised = int(r.hget(chat_id_meta_string, 'finalised'))

    if user_id_string not in orders:
        context.bot.send_message(chat_id=chat_id,
                                 text="Sorry, you are not in the current jio. 😢")
    elif finalised == 0:
        context.bot.send_message(chat_id=chat_id,
                                 text="Please wait for the jio to be finalised.")
    else:
        original_message = orders[user_id_string]

        # Do nothing is user has paid
        if '✅' in original_message:
            return

        # Mark as paid if user has not paid.
        order_message = original_message + ' ✅'

        orders[user_id_string] = order_message
        r.hmset(chat_id_item_string, orders)

        # Form updated message
        jio_name = r.hget(chat_id_meta_string, 'title')
        updated_orders = '\n'.join(['%s' % value for value in orders.values()])
        reply = get_finalised_jio_name_string(jio_name) + updated_orders
        context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply, parse_mode= 'html')

        # Check if everyone paid, if so, end the jio.
        everyone_paid = True
        for order in orders.values():
            if '✅' not in order:
                everyone_paid = False
        
        if everyone_paid:
            r.delete(chat_id_meta_string)
            r.delete(chat_id_item_string)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                text="Everyone paid! Jio session ended. 🥳")
    
# End a jio in the group
def end_jio(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return

    jio_name = r.hget(chat_id_meta_string, 'title')

    # Delete existing data of the current jio
    r.delete(chat_id_meta_string)
    r.delete(chat_id_item_string)
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="Your current jio " + "is terminated. See you next time!")

# Finalise the jio so that users can mark their orders as paid
def finalise_jio(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # Guard clause against user edited message
    if user_id == 0 or user_name == '':
        return
    
    if not r.hget(chat_id_meta_string, 'message_id'):
        context.bot.send_message(chat_id=chat_id,
                                 text="No jio currently. Start a jio with '/start_jio <title>'")
        return
    
    orders = r.hgetall(chat_id_item_string)
    metadata =  r.hgetall(chat_id_meta_string)

    if metadata['finalised'] == 1:
        context.bot.send_message(chat_id=chat_id,
                                 text="The jio is empty. To end the jio, use '/end_jio'")
        return
    
    if not orders:
        context.bot.send_message(chat_id=chat_id,
                                 text="The jio is empty. To end the jio, use '/end_jio'")
        return
    
    # Form new message
    # jio_name = r.hget(chat_id_meta_string, 'title')
    # orders = '\n'.join(['%s' % value for value in orders.values()])
    reply = "Are you sure you want to finalise the jio?"
    
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data='confirm_finalise'),
            InlineKeyboardButton("No", callback_data='cancel')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = context.bot.send_message(chat_id, text=reply, parse_mode= 'html', reply_markup=reply_markup)

    # Update message_id to the finalised message
    metadata['message_id'] = message.message_id
    r.hmset(chat_id_meta_string, metadata)

def cancel(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))

    context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Don't play play ah! 😠")


# Confirmation to finalise jio, finalising a jio is irreversible
def confirm_finalise_jio(update, context):
    r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

    arguments, user_id, user_name, chat_id = parse(update, context)
    chat_id_meta_string, chat_id_item_string, user_id_string = stringify_ids(chat_id, user_id)

    # # Guard clause against user edited message
    # if user_id == 0 or user_name == '':
    #     return
    
    orders = r.hgetall(chat_id_item_string)
    metadata =  r.hgetall(chat_id_meta_string)
    
    # Form new message
    jio_name = r.hget(chat_id_meta_string, 'title')
    orders = '\n'.join(['%s' % value for value in orders.values()])
    reply = get_finalised_jio_name_string(jio_name) + orders
    message_id = int(r.hget(chat_id_meta_string, 'message_id'))

    message = context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply, parse_mode= 'html')
    
    # Set finalised to true
    metadata['finalised'] = 1

    # Update message_id to the finalised message
    metadata['message_id'] = message.message_id
    r.hmset(chat_id_meta_string, metadata)
