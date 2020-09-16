from io import BytesIO
from time import sleep
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import is_user_ban_protected, bot_admin

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4


@run_async
def quickscope(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("ඔබ චැට් / පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ")
    try:
        bot.kick_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Attempted banning " + to_kick + " from" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def quickunban(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("ඔබ චැට් / පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ")
    try:
        bot.unban_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("Attempted unbanning " + to_kick + " from" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def banall(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[0])
        all_mems = sql.get_chat_members(chat_id)
    else:
        chat_id = str(update.effective_chat.id)
        all_mems = sql.get_chat_members(chat_id)
    for mems in all_mems:
        try:
            bot.kick_chat_member(chat_id, mems.user)
            update.effective_message.reply_text("Tried banning " + str(mems.user))
            sleep(0.1)
        except BadRequest as excp:
            update.effective_message.reply_text(excp.message + " " + str(mems.user))
            continue


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("කරුණාකර මට ප්‍රතිරාවය කිරීමට චැට් එකක් දෙන්න!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text("පණිවිඩය යැවීමට නොහැකි විය. සමහර විට මම එම කණ්ඩායමේ සාමාජිකයෙක් නොවේද?")


@run_async
@bot_admin
def getlink(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        update.effective_message.reply_text("ඔබ කතාබහකට යොමු වූ බවක් නොපෙනේ")
    chat = bot.getChat(chat_id)
    bot_member = chat.get_member(bot.id)
    if bot_member.can_invite_users:
        invitelink = bot.get_chat(chat_id).invite_link
        update.effective_message.reply_text(invitelink)
    else:
        update.effective_message.reply_text("මට ආරාධනා සබැඳියට ප්‍රවේශය නැත!")


@bot_admin
def leavechat(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
        bot.leaveChat(chat_id)
    else:
        update.effective_message.reply_text("ඔබ කතාබහකට යොමු වූ බවක් නොපෙනේ")

__help__ = """
**හිමිකරු පමණි:**
- /getlink **chatid**: විශේෂිත කතාබස් සඳහා ආරාධනා සබැඳිය ලබා ගන්න.
- /banall: සියලුම සාමාජිකයන් සංවාදයකින් තහනම් කරන්න
- /leavechat **chatid** :කතාබස් කරන්න
**සුඩෝ / හිමිකරු පමණි:**
- /quickscope **userid** **chatid**: පරිශීලකයා කතාබස් කිරීමෙන් තහනම් කරන්න.
- /quickunban **userid** **chatid**: චැට් වලින් ඉවත් කරන්න.
- /snipe **chatid** **string**: විශේෂිත කතාබහකට මට පණිවිඩයක් යැවීමට සලස්වන්න.
- /rban **userid** **chatid** :චැට් එකකින් පරිශීලකයෙකු දුරස්ථව තහනම් කරන්න
- /runban **userid** **chatid** :චැට් එකකින් පරිශීලකයෙකු දුරස්ථව තහනම් කරන්න
- /Stats: check bot's stats
- /chatlist: චැට්ලිස්ට් ලබා ගන්න
- /gbanlist: gbanned පරිශීලක ලැයිස්තුව ලබා ගන්න
- /gmutelist:gmuted පරිශීලක ලැයිස්තුව ලබා ගන්න
- Chat bans via /restrict chat_id and /unrestrict chat_id commands
**සහාය පරිශීලකයා:**
- /Gban : ගෝලීය තහනමක් පරිශීලකයෙකුට
- /Ungban : Ungban පරිශීලකයෙක්
- /Gmute : පරිශීලකයෙකු මැලියම් කරන්න
- /Ungmute : පරිශීලකයෙකු ඉවත් කරන්න
Sudo/owner මෙම විධානයන් ද භාවිතා කළ හැකිය.
**පරිශීලකයින්:**
- /listsudo සුඩෝ භාවිතා කරන්නන්ගේ ලැයිස්තුවක් ලබා දෙයි
- /listsupport සහාය පරිශීලකයින්ගේ ලැයිස්තුවක් ලබා දෙයි
"""
__mod_name__ = "Special"

SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=CustomFilters.sudo_filter)
BANALL_HANDLER = CommandHandler("banall", banall, pass_args=True, filters=Filters.user(OWNER_ID))
QUICKSCOPE_HANDLER = CommandHandler("quickscope", quickscope, pass_args=True, filters=CustomFilters.sudo_filter)
QUICKUNBAN_HANDLER = CommandHandler("quickunban", quickunban, pass_args=True, filters=CustomFilters.sudo_filter)
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler("leavechat", leavechat, pass_args=True, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
dispatcher.add_handler(QUICKSCOPE_HANDLER)
dispatcher.add_handler(QUICKUNBAN_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
