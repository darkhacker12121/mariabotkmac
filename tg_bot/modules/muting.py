import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("නිශ්ශබ්ද කිරීම සඳහා ඔබට පරිශීලක නාමයක් ලබා දීමට හෝ නිශ්ශබ්ද කිරීමට යමෙකුට පිළිතුරු දීමට ඔබට අවශ්‍ය වනු ඇත.")
        return ""

    if user_id == bot.id:
        message.reply_text("මම මා ගැනම කතා කරන්නේ නැහැ!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("බියෙන් මට පරිපාලකයෙකු කතා කිරීම නතර කළ නොහැක!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            message.reply_text("👍🏻 නිශ්ශබ්ද විය! 🤐")
            return "<b>{}:</b>" \
                   "\n#MUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් නිශ්ශබ්ද කර ඇත!)
    else:
        message.reply_text("මෙම පරිශීලකයා සංවාදයේ නොමැත!")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("එක්කෝ ඔබ මට නිශ්ශබ්ද කිරීමට පරිශීලක නාමයක් ලබා දිය යුතුය, නැතහොත් නිශ්ශබ්ද වීමට යමෙකුට පිළිතුරු දිය යුතුය.")
        return ""

    member = chat.get_member(int(user_id))

    if member.status != 'kicked' and member.status != 'left':
        if member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text("This user already has the right to speak.")
        else:
            bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
            message.reply_text("Unmuted!")
            return "<b>{}:</b>" \
                   "\n#UNMUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))
    else:
        message.reply_text("මෙම පරිශීලකයා කතාබස්වල පවා නොසිටින අතර, ඒවා නිශ්ක්‍රීය කිරීමෙන් ඔවුන්ට වඩා කතා කිරීමට නොහැකි වනු ඇත "
                           "දැනටමත් කරන්න!")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
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

    if is_user_admin(chat, user_id, member):
        message.reply_text("මම ඇත්තටම ප්‍රාර්ථනා කරනවා මට පරිපාලකයින් නිශ්ශබ්ද කරන්න ... ")
        return ""

    if user_id == bot.id:
        message.reply_text("මම තනියම නිශ්ශබ්ද වෙන්නෙ නෑ, ඔයාට පිස්සුද?")
        return ""

    if not reason:
        message.reply_text("මෙම පරිශීලකයා නිශ්ශබ්ද කිරීමට ඔබ කාලයක් නියම කර නැත!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP MUTED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            message.reply_text("කට වහපන්! 😠 නිශ්ශබ්ද කර ඇත {}!".format(time_val))
            return log
        else:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් නිශ්ශබ්ද කර ඇත.")

    except BadRequest as excp:
        if excp.message == "පිළිතුරු පණිවිඩය හමු නොවීය":
            # Do not reply
            message.reply_text("කට වහපන්! 😠 නිශ්ශබ්ද කර ඇත {}!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("දෝෂ නිශ්ශබ්ද කිරීම user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("හොඳයි, මට එම පරිශීලකයා නිශ්ශබ්ද කළ නොහැක.")

    return ""


__help__ = """
*පරිපාලක පමණි:*
 - /mute <userhandle>: පරිශීලකයෙකු නිහ ces කරයි. පිළිතුරක් ලෙස භාවිතා කළ හැකිය, පිළිතුරු පරිශීලකයාට නිශ්ශබ්ද කිරීම.
 - /tmute <userhandle> x(m/h/d): mx කාලය සඳහා පරිශීලකයෙකු භාවිතා කරයි. (හසුරුව හරහා හෝ පිළිතුරු දෙන්න). m = minutes, h = hours, d = days.
 - /unmute <userhandle>: පරිශීලකයෙකු ඉවත් කරයි. පිළිතුරක් ලෙස භාවිතා කළ හැකිය, පිළිතුරු පරිශීලකයාට නිශ්ශබ්ද කිරීම.
"""

__mod_name__ = "Mute"

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True, filters=Filters.group)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
