import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text("අන් අයට බාධා නොකරන්න ඔබ තවදුරටත් මෙම කණ්ඩායමට අවශ්‍ය නැත...")

        return "<b>{}:</b>" \
               "\n#BANNED" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("ඔබ මට අවසර ලබා නොදෙන තාක් කල් ඔබට මෙම සේවාව භාවිතා කළ නොහැක.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nකික් අවසර නැත, එබැවින් ස්වයංක්‍රීයව ඇන්ටිෆ්ලූඩ් අක්‍රීය කරන්න.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("flood ඇති අයව මම තවදුරටත් ඉවත් නොකරමි.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("flood ඇති අයව මම තවදුරටත් ඉවත් නොකරමි.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisabled antiflood.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text("ඇන්ටිෆ්ලූඩ් ද විය යුතුය 0 (disabled), හෝ වඩා විශාල සංඛ්‍යාවක් 3!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("පණිවිඩ පාලනය {} ගණන් කිරීමට එකතු කර ඇත ".format(amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("ඔබ කියන දේ මට තේරෙන්නේ නැත .... එක්කෝ අංකය භාවිතා කරන්න හෝ භාවිතා කරන්න Yes-No")

    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("මම දැන් පණිවිඩ පාලනය කරන්නේ නැහැ!")
    else:
        update.effective_message.reply_text(
            " {} මම එකවරම පණිවිඩය යවන පුද්ගලයාට bun තබමි.".format(limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "*Not* දැනට flood පාලනය බලාත්මක කරයි."
    else:
        return "පණිවිඩ පාලනය සකසා ඇත`{}`.".format(limit)


__help__ = """
 - /flood: ඔබගේ වර්තමාන පණිවිඩ පාලනය දැන ගැනීමට..

*Admin only:*
 - /setflood <int/'no'/'off'>: flood  පාලනය සක්‍රීය හෝ අක්‍රීය කරයි
"""

__mod_name__ = "AntiFlood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
