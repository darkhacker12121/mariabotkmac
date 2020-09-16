import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය kick  ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

RUNBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට  ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "මූලික කණ්ඩායමකින් එය kick  ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

RKICK_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට  ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "මූලික කණ්ඩායමකින් එය kick  ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

RMUTE_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට  ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "මූලික කණ්ඩායමකින් එය kick  ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

RUNMUTE_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට  ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "මූලික කණ්ඩායමකින් එය kick  ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("“ඔබ සඳහන් කරන බවක් නොපෙනේ chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return
    elif not chat_id:
        message.reply_text("ඔබ කතාබහකට යොමු වූ බවක් නොපෙනේ.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "චැට් හමු නොවීය":
            message.reply_text("චැට් හමු නොවීය! ඔබ වලංගු චැට් හැඳුනුම්පතක් ඇතුළත් කළ බවට වග බලා ගන්න, මම එම සංවාදයේ කොටසක් වෙමි.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("මට කණගාටුයි, නමුත් එය පෞද්ගලික කතාබහකි!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("මට එහි මිනිසුන් සීමා කළ නොහැක! මම පරිපාලක බවට වග බලා ගන්න සහ පරිශීලකයින් තහනම් කළ හැකිය.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("මට මෙම පරිශීලකයා සොයා ගත නොහැක")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Iඇත්තටම ප්‍රාර්ථනා කරනවා මට පරිපාලකයින් තහනම් කරන්න ...")
        return

    if user_id == bot.id:
        message.reply_text("මම තනියම යන්නෙ නෑ, ඔයාට පිස්සුද?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("කතාබස් කිරීම තහනම්!")
    except BadRequest as excp:
        if excp.message == "පිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(දෝෂය තහනම් කිරීමuser %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා තහනම් කළ නොහැක.)

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("ඔබ කතාබස් / පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return
    elif not chat_id:
        message.reply_text("ඔබ කතාබහකට යොමු වූ බවක් නොපෙනේ.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "චැට් හමු නොවීය":
            message.reply_text("චැට් හමු නොවීය! ඔබ වලංගු චැට් හැඳුනුම්පතක් ඇතුළත් කළ බවට වග බලා ගන්න, මම එම සංවාදයේ කොටසක් වෙමි.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("මට කණගාටුයි, නමුත් එය පෞද්ගලික කතාබහකි!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("මට එහි මිනිසුන්ව පාලනය කළ නොහැක! මම පරිපාලක බවට වග බලා ගන්න සහ පරිශීලකයින් තහනම් කළ හැකිය.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "පරිශීලකයා හමු නොවීය ":
            message.reply_text("මට මෙම පරිශීලකයා එහි සිටින බවක් නොපෙනේ")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("එම සංවාදයේ දැනටමත් සිටින අයෙකු දුරස්ථව තහනම් කිරීමට ඔබ උත්සාහ කරන්නේ ඇයි?")
        return

    if user_id == bot.id:
        message.reply_text("මම UNBAN යන්නෙ නෑ, මම එහි පරිපාලකයෙක්!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("ඔව්, මෙම පරිශීලකයාට එම කතාබහට සම්බන්ධ විය හැකිය!")
    except BadRequest as excp:
        if excp.message == "පිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't unban that user.")

@run_async
@bot_admin
def rkick(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("චැට් හමු නොවීය! ඔබ වලංගු චැට් හැඳුනුම්පතක් ඇතුළත් කළ බවට වග බලා ගන්න, මම එම සංවාදයේ කොටසක් වෙමි.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("මට එහි මිනිසුන් සීමා කළ නොහැක! මම පරිපාලක බවට වග බලා ගන්න සහ පරිශීලකයින්ට පයින් ගසන්නට පුළුවන.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I really wish I could kick admins...")
        return

    if user_id == bot.id:
        message.reply_text("I'm not gonna KICK myself, are you crazy?")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Kicked from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Kicked!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR kicking user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't kick that user.")

@run_async
@bot_admin
def rmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("I can't restrict people there! Make sure I'm admin and can mute users.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I really wish I could mute admins...")
        return

    if user_id == bot.id:
        message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return

    try:
        bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
        message.reply_text("Muted from the chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Muted!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR mute user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't mute that user.")

@run_async
@bot_admin
def runmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("ඔබ කතාබස් / පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return
    elif not chat_id:
        message.reply_text("ඔබ කතාබහකට යොමු වූ බවක් නොපෙනේ.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("චැට් හමු නොවීය! ඔබ වලංගු චැට් හැඳුනුම්පතක් ඇතුළත් කළ බවට වග බලා ගන්න, මම එම සංවාදයේ කොටසක් වෙමි.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("මට එහි මිනිසුන්ව පාලනය කළ නොහැක! මම පරිපාලක බවට වග බලා ගන්න සහ පරිශීලකයින් තහනම් කළ හැකිය.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("මට මෙම පරිශීලකයා එහි සිටින බවක් නොපෙනේ")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
       if member.can_send_messages and member.can_send_media_messages \
          and member.can_send_other_messages and member.can_add_web_page_previews:
        message.reply_text("මෙම කතාබහ තුළ කතා කිරීමට මෙම පරිශීලකයාට දැනටමත් අයිතියක් ඇත.")
        return

    if user_id == bot.id:
        message.reply_text("මම මාවම පාලනය කරන්න යන්නේ නැහැ, මම එහි පරිපාලකයෙක්! ”)
        return

    try:
        bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
        message.reply_text("Yep, this user can talk in that chat!")
    except BadRequest as excp:
        if excp.message == "Rපිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text('Unmuted!', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("දෝෂ ඉවත් කිරීම user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා ඉවත් කළ නොහැක.")

__help__ = ""

__mod_name__ = "Remote Commands"

RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler("rkick", rkick, pass_args=True, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler("rmute", rmute, pass_args=True, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler("runmute", runmute, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
