from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(user.id, "මෙම කතාබස් සඳහා නීති කෙටිමං නිසි ලෙස සකසා නැත! පරිපාලකයින්ගෙන් විමසන්න "
                                      "මෙය නිවැරදි කරන්න.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "The rules for *{}* are:\n\n{}".format(escape_markdown(chat.title), rules)

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(user.id, "කණ්ඩායම් පරිපාලකයින් මෙම කතාබහ සඳහා තවමත් නීති රීති සකසා නැත. "
                                  "මෙය බොහෝ විට එය නීති විරෝධී යැයි අදහස් නොකෙරේ ...!")
    elif rules:
        update.effective_message.reply_text("මෙම කණ්ඩායමේ නීති ලබා ගැනීම සඳහා මාව PM හි අමතන්න.",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="Rules",
                                                                       url="t.me/{}?start={}".format(bot.username,
                                                                                                     chat_id))]]))
    else:
        update.effective_message.reply_text("කණ්ඩායම් පරිපාලකයින් මෙම කතාබහ සඳහා තවමත් නීති රීති සකසා නැත. "
                                            "මෙය බොහෝ විට එය නීති විරෝධී යැයි අදහස් නොකෙරේ ...!")


@run_async
@user_admin
def set_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("මෙම කණ්ඩායම සඳහා නීති සාර්ථකව සකසන්න.")


@run_async
@user_admin
def clear_rules(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("නීති සාර්ථකව ඉවත් කර ඇත!)


def __stats__():
    return "{} කතාබස් වලට නීති රීති ඇත.".format(sql.num_chats())


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "මෙම කතාබහට එහි නීති රීති සකසා ඇත: `{}`".format(bool(sql.get_rules(chat_id)))


__help__ = """
 - /rules:මෙම කතාබහ සඳහා නීති ලබා ගන්න.

*පරිපාලක පමණි:*
 - /setrules <your rules here>: මෙම කතාබහ සඳහා නීති සකසන්න.
 - /clearrules: මෙම කතාබහ සඳහා නීති ඉවත් කරන්න.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
