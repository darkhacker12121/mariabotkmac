import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

import tg_bot.modules.sql.blacklist_sql as sql
from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin, user_not_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.misc import split_message

BLACKLIST_GROUP = 11

BASE_BLACKLIST_STRING = "Current <b>blacklisted</b> words:\n"


@run_async
def blacklist(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    filter_list = BASE_BLACKLIST_STRING

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if text == BASE_BLACKLIST_STRING:
            msg.reply_text("මෙහි අසාදු ලේඛණගත පණිවිඩ නොමැත!")
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_blacklist(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat.id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text("Added <code>{}</code> to the blacklist!".format(html.escape(to_blacklist[0])),
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                "Added <code>{}</code> triggers to the blacklist.".format(len(to_blacklist)), parse_mode=ParseMode.HTML)

    else:
        msg.reply_text("අසාදු ලේඛනයෙන් ඉවත් කිරීමට ඔබ කැමති වචන මොනවාදැයි මට කියන්න.")


@run_async
@user_admin
def unblacklist(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    words = msg.text.split(None, 1)
    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text("Removed <code>{}</code> from the blacklist!".format(html.escape(to_unblacklist[0])),
                               parse_mode=ParseMode.HTML)
            else:
                msg.reply_text("මෙය අසාදු ලේඛණගත කළ ප්‍රේරකයක් නොවේ ...!")

        elif successful == len(to_unblacklist):
            msg.reply_text(
                "Removed <code>{}</code> triggers from the blacklist.".format(
                    successful), parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text(
                "මෙම ප්‍රේරක කිසිවක් නොපවතින බැවින් ඒවා ඉවත් නොකෙරුණි.".format(
                    successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                "Removed <code>{}</code> triggers from the blacklist. {} did not exist, "
                "එබැවින් ඉවත් නොකළේය.".format(successful, len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)
    else:
        msg.reply_text("අසාදු ලේඛනයෙන් ඉවත් කිරීමට ඔබ කැමති වචන මොනවාදැයි මට කියන්න.")


@run_async
@user_not_admin
def del_blacklist(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "මැකීමට පණිවිඩය හමු නොවීය":
                    pass
                else:
                    LOGGER.exception("අසාදු ලේඛණ පණිවිඩය මැකීමේදී දෝෂයකි.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "There are {} blacklisted words.".format(blacklisted)


def __stats__():
    return "{} blacklist triggers, across {} chats.".format(sql.num_blacklist_filters(),
                                                            sql.num_blacklist_filter_chats())


__mod_name__ = "Word Blacklists"

__help__ = """
සමහර ප්‍රේරක සමූහයක් තුළ පැවසීම වැළැක්වීමට අසාදු ලේඛණ භාවිතා කරයි. ප්‍රේරකය සඳහන් කරන ඕනෑම වේලාවක, \
පණිවිඩය වහාම මකා දැමෙනු ඇත. හොඳ සංයෝජනයක් සමහර විට මෙය අනතුරු ඇඟවීමේ පෙරහන් සමඟ සම්බන්ධ කිරීමකි!

*සටහන:* අසාදු ලේඛණ කණ්ඩායම් පරිපාලකයින්ට බලපාන්නේ නැත.

 - /blacklist: දැනට ලැයිස්තුගත කර ඇති වචන බලන්න.

*Admin only:*
 - /addblacklist <triggers>: අසාදු ලේඛනයට ප්‍රේරකයක් එක් කරන්න. සෑම පේළියක්ම එක් ප්‍රේරකයක් ලෙස සලකනු ලැබේ, එබැවින් වෙනස් using භාවිතා කිරීම
පේළි මඟින් ඔබට බහු ප්‍රේරක එකතු කිරීමට ඉඩ ලබා දේ.
 - /unblacklist <triggers>: අසාදු ලේඛනයෙන් ප්‍රේරක ඉවත් කරන්න. එකම නව රේඛා තර්කනය මෙහි අදාළ වේ, එවිට ඔබට remove ඉවත් කළ හැකිය
එකවර බහු ප්‍රේරක.
 - /rmblacklist <triggers>: ඉහත ආකාරයටම.
"""

BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist, filters=Filters.group, pass_args=True,
                                              admin_ok=True)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist, filters=Filters.group)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"], unblacklist, filters=Filters.group)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
