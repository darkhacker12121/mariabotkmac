import html
from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.userinfo_sql as sql
from tg_bot import dispatcher, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user


@run_async
def about_me(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + "ඔහු පිළිබඳ තොරතුරු දැනට නොමැත!")
    else:
        update.effective_message.reply_text("ඔබ තවමත් ඔබ ගැන කිසිදු තොරතුරක් එකතු කර නැත!")


@run_async
def set_about_me(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            message.reply_text("ඔබේ තොරතුරු සාර්ථකව පටිගත කර ඇත")
        else:
            message.reply_text(
                " ඔයා ගැන{} අකුරු වලට සීමා වීම ".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


@run_async
def about_bio(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text("{} ඔහු ගැන කිසිදු විස්තරයක් තවම එකතු කර නැත!".format(username))
    else:
        update.effective_message.reply_text(" ඔබ පිළිබඳ ඔබේ තොරතුරු එකතු කර ඇත!")


@run_async
def set_about_bio(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text("ඔබ ඔබේම වෙනස් කිරීමට බලා සිටිනවාද ... ?? ඒක තමයි.")
            return
        elif user_id == bot.id and sender.id not in SUDO_USERS:
            message.reply_text(" මගේ තොරතුරු වෙනස් කළ හැක්කේ SUDO පරිශීලකයින්ට පමණි.")
            return

        text = message.text
        bio = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("{} ඔහු පිළිබඳ තොරතුරු සාර්ථකව එකතු කර ඇත!".format(repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "ඔයා ගැන {} ලිපියට ඇලී සිටිය යුතුය! ඔබ දැන් උත්සාහ කර ඇති චරිත ගණන {} hm .".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text(" ඔහුගේ තොරතුරු එක් කළ හැක්කේ යමෙකුගේ පණිවිඩය පිළිතුරක් ලෙස නම් පමණි")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return "<b>පරිශීලකයා ගැන:</b>\n{me}\n<b>What others say:</b>\n{bio}".format(me=me, bio=bio)
    elif bio:
        return "<b>අනිත් අය කියන දේ:</b>\n{bio}\n".format(me=me, bio=bio)
    elif me:
        return "<b>පරිශීලකයා ගැන:</b>\n{me}""".format(me=me, bio=bio)
    else:
        return ""


__help__ = """
 - /setbio <text>: පිළිතුරු දෙන අතරතුර, වෙනත් පරිශීලකයෙකුගේ ජෛව සුරකිනු ඇත
 - /bio: ඔබේ හෝ වෙනත් පරිශීලකයෙකුගේ ජීව දත්ත ලබා ගනී. මෙය ඔබටම සැකසිය නොහැක.
 - /setme <text>: ඔබගේ තොරතුරු සැකසෙනු ඇත
 - /me: ඔබගේ හෝ වෙනත් පරිශීලකයෙකුගේ තොරතුරු ලැබෙනු ඇත
"""

__mod_name__ = "Bios and Abouts"

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio, pass_args=True)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me, pass_args=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)
