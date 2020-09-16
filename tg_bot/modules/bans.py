import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා කිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවේ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය  kick ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට  kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

RUNBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා කිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවේ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය  kick ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට  kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("මට මෙම පරිශීලකයා සොයා ගත නොහැක")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("මම ඇත්තටම පරිපාලකයින් තහනම් කරන්න කැමතියි...🤗🤗")
        return ""

    if user_id == bot.id:
        message.reply_text("මම යන්නේ නැහැ තහනම් කරන්න මා, ඔයාට පිස්සු ද?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} Banned!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා තහනම් කළ නොහැක.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "පරිශීලකයා හමු නොවීය":
            message.reply_text("මට මෙම පරිශීලකයා සොයා ගත නොහැක")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("මම ඇත්තටම පරිපාලකයින් තහනම් කරන්න කැමතියි...🤗🤗")
        return ""

    if user_id == bot.id:
        message.reply_text("මම යන්නේ නැහැ තහනම් කරන්න මා, ඔයාට පිස්සු ද?")
        return ""

    if not reason:
        message.reply_text("මෙම පරිශීලකයා තහනම් කිරීමට ඔබ කාලයක් නියම කර නැත!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("තහනම්! පරිශීලකයා සඳහා තහනම් කරනු ලැබේ {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "පිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text("තහනම්! පරිශීලකයා සඳහා තහනම් කරනු ලැබේ {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("දෝෂ තහනම් කිරීම user %s තුල chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා තහනම් කළ නොහැක.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("මට මෙම පරිශීලකයා සොයා ගත නොහැක")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("මම ඇත්තටම පරිපාලකයින් තහනම් කරන්න කැමතියි...🤗🤗")
        return ""

    if user_id == bot.id:
        message.reply_text("ඔව්, මම ඒක කරන්න යන්නේ නැහැ")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!🚫")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("හොඳයි, මට ඒ පරිශීලකයාට Kick ගහන්න බැහැ.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("මම ප්‍රාර්ථනා කරනවා මට පුළුවන් ... ඒත් ඔයා පරිපාලකයෙක්.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("කිසිම ප්රශ්නයක් නැ.")
    else:
        update.effective_message.reply_text("හහ්? මට බැහැ :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("මට මෙම පරිශීලකයා සොයා ගත නොහැක")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("මම මෙහි නොසිටියේ නම් මා කෙසේ තහනම් කරන්නේද?...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("ඔබ දැනටමත් සංවාදයේ යෙදී සිටින අයෙකු තහනම් කිරීමට උත්සාහ කරන්නේ ඇයි??")
        return ""

    chat.unban_member(user_id)
    message.reply_text("ඔව්, මෙම පරිශීලකයාට සම්බන්ධ විය හැකිය!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("ඔබ යොමු දක්වන්නේ  chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ යොමු දක්වන්නේ  user.")
        return
    elif not chat_id:
        message.reply_text("ඔබ සඳහන් කරන බවක් නොපෙනේ chat.")
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
        message.reply_text("මම ඇත්තටම පරිපාලකයින් තහනම් කරන්න කැමතියි...🤗🤗")
        return

    if user_id == bot.id:
        message.reply_text("ඔව්, මම ඒක කරන්න යන්නේ නැහැ")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Banned!")
    except BadRequest as excp:
        if excp.message == "පිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("දෝෂය තහනම් කිරීම user %s තුල chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා තහනම් කළ නොහැක.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("ඔබ යොමු දක්වන්නේ chat/user.")
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
        message.reply_text("මට කණගාටුයි, නමුත් එය පෞද්ගලික කතාබහකි!")
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
        message.reply_text("එම සංවාදයේ දැනටමත් සිටින අයෙකු දුරස්ථව තහනම් කිරීමට ඔබ උත්සාහ කරන්නේ ඇයි?")
        return

    if user_id == bot.id:
        message.reply_text("මම මාවම තහනම් කරන්න යන්නේ නැහැ, මම එහි පරිපාලකයෙක්!")
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
            LOGGER.exception("දෝෂය තහනම් කිරීම user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා තහනම් කළ නොහැක.")


__help__ = """
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /ban <userhandle>: පරිශීලකයෙකු තහනම් කරයි. (හසුරුව හරහා, or පිලිතුරු)
 - /tban <userhandle> x(m/h/d): x කාලය සඳහා පරිශීලකයෙකුට තහනම් කරයි. (හසුරුව හරහා, or පිලිතුරු). m = minutes, h = hours, d = days.
 - /unban <userhandle>: පරිශීලකයෙකු  තහනම ඉවත් කිරීම .(හසුරුව හරහා, or පිලිතුරු)
 - /kick <userhandle>: kicks පරිශීලකයෙක්, (හසුරුව හරහා, or පිලිතුරු)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
