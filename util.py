
def parse(update, context):
    arguments = context.args
    user_id = update.message.from_user.id
    user_name = update.message.from_user.name
    chat_id = update.effective_chat.id
    return arguments, user_id, user_name, chat_id


def stringify_ids(chat_id, user_id):
    chat_id_meta_string = get_chat_id_meta_string(chat_id)
    chat_id_item_string = get_chat_id_item_string(chat_id)
    user_id_string = get_user_id_string(user_id)
    return chat_id_meta_string, chat_id_item_string, user_id_string


def get_chat_id_meta_string(chat_id):
    return 'meta' + str(chat_id)


def get_chat_id_item_string(chat_id):
    return 'item' + str(chat_id)


def get_user_id_string(user_id):
    return 'u' + str(user_id)
