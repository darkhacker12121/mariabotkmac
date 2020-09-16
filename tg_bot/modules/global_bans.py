import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය පයින් ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
    "කණ්ඩායම් පරිපාලකයින්ට Kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි",
    "නාලිකාව_පුද්ගලිකයි",
    "චැට් එකේ නැහැ"
}

UNGBAN_ERRORS = {
    "පරිශීලකයා චැට් හි පරිපාලකයෙකි",
    "චැට් හමු නොවීය",
    "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත",
    "පරිශීලකයා_සහභාගී_නොවෙ ",
    "තුල්‍ය _ැඳුනුම්පත_අවලංගුය",
    "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි",
    "මූලික කණ්ඩායමකින් එය පයින් ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය",
    "චැට්_පරිපාලක_අවශ්‍යයි",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("මම ඔත්තු බැලුවෙමි, මගේ කුඩා ඇසෙන් ... සුඩෝ පරිශීලක යුද්ධයක්! ඇයි ඔයාලා එකිනෙකාට හරවන්නේ?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH යමෙක් ආධාරක පරිශීලකයෙකු අල්ලා ගැනීමට උත්සාහ කරයි! *මත් එක්ක ඒවා නම් බැ මහත්තයෝ 😎😎*")
        return

    if user_id == bot.id:
        message.reply_text("-_- හරිම විහිලුයි, ඇයි මම නැත්තේ? හොඳයි උත්සාහ කරන්න.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("එය පරිශීලකයෙකු නොවේ!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් gbanned; මම හේතුව වෙනස් කරන්නම්, නමුත් ඔබ මට එකක් දුන්නේ නැහැ ...🥺😩")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text("පහත සඳහන් හේතුව නිසා මෙම පරිශීලකයා දැනටමත් gbanned කර ඇත:\n"
                               "<code>{}</code>\n"
                               "මම ගොස් ඔබගේ නව හේතුව සමඟ එය යාවත්කාලීන කර ඇත!".format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)
        else:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් අවහිර කර ඇත, නමුත් කිසිදු හේතුවක් සකසා නැත; මම ගොස් එය යාවත්කාලීන කර ඇත!")

        return

    message.reply_text("⚡️ *Snaps the Banhammer* ⚡️")

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Global Ban</b>" \
                 "\n#GBAN" \
                 "\n<b>Status:</b> <code>Enforcing</code>" \
                 "\n<b>Sudo Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>" \
                 "\n<b>Reason:</b> {}".format(mention_html(banner.id, banner.first_name),
                                              mention_html(user_chat.id, user_chat.first_name), 
                                                           user_chat.id, reason or "No reason given"), 
                html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("මේ නිසා gban කිරීමට නොහැකි විය: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "මේ නිසා gban කිරීමට නොහැකි විය: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} hසාර්ථකව ගැබ් කර ඇති පරිදි!".format(mention_html(user_chat.id, user_chat.first_name)),
                html=True)
    message.reply_text("Person has been gbanned.")


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("එය පරිශීලකයෙකු නොවේ!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("මෙම පරිශීලකයා gbanned නොවේ!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("මම සමාව දෙනවා {}, ගෝලීය වශයෙන් දෙවන අවස්ථාව සමඟ.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>Regression of Global Ban</b>" \
                 "\n#UNGBAN" \
                 "\n<b>Status:</b> <code>Ceased</code>" \
                 "\n<b>Sudo Admin:</b> {}" \
                 "\n<b>User:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),
                                                       mention_html(user_chat.id, user_chat.first_name), 
                                                                    user_chat.id),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text("නිසා un-gban කිරීමට නොහැකි විය: {}".format(excp.message))
                bot.send_message(OWNER_ID, "නිසා un-gban කිරීමට නොහැකි විය: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} gban වෙතින් සමාව ලැබී ඇත!".format(mention_html(user_chat.id, 
                                                                         user_chat.first_name)),
                  html=True)

    message.reply_text("මෙම පුද්ගලයාට තහනම් කර ඇති අතර සමාව දෙනු ලැබේ!")


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("Gbanned භාවිතා කරන්නන් නොමැත! මම හිතුවට වඩා ඔයා කරුණාවන්තයි ...🤗🥰")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="දැනට gbanned භාවිතා කරන්නන්ගේ ලැයිස්තුව මෙන්න.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("මේක නරක පුද්ගලයෙක්, ඔවුන් මෙහි නොසිටිය යුතුයි!")


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("මම මෙම කණ්ඩායමේ gbans සක්‍රීය කර ඇත. මෙය ඔබව ආරක්ෂා කිරීමට උපකාරී වේ "
                                                "අයාචිත තැපැල්, අප්‍රසන්න චරිත සහ විශාලතම ට්‍රෝලර් වලින්.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("මම මෙම කණ්ඩායමේ gbans අක්‍රීය කර ඇත. GBans ඔබගේ පරිශීලකයින්ට බලපාන්නේ නැත "
                                                "තවදුරටත්. ඕනෑම ට්‍රෝලර් සහ ස්පෑම්කරුවන්ගෙන් ඔබව අඩු ආරක්ෂාවක් ලැබෙනු ඇත "
                                                "නමුත්!")
    else:
        update.effective_message.reply_text("Gපසුබිමක් තෝරා ගැනීමට මට තර්ක කිහිපයක් ඉදිරිපත් කරන්න! on/off, yes/no!\n\n"
                                            "ඔබගේ වර්තමාන සැකසුම: {}\n"
                                            "සත්‍ය වූ විට, සිදුවන ඕනෑම gban ඔබේ කණ්ඩායම තුළ ද සිදුවනු ඇත."
                                            "අසත්‍ය වූ විට, ඔවුන් එසේ නොකරනු ඇත "
                                            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} gbanned users.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "Globally banned: <b>{}</b>"
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gbans*: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = """
*පරිපාලක පමණි:*
 - /gbanstat <on/off/yes/no>:ඔබගේ කණ්ඩායමට ගෝලීය තහනමේ බලපෑම අක්‍රීය කරනු ඇත, නැතහොත් ඔබගේ වර්තමාන සැකසුම් නැවත ලබා දෙනු ඇත.

ගෝලීය තහනම ලෙසද හැඳින්වෙන ග්බාන්ස්, සියලුම කණ්ඩායම් හරහා අයාචිත තැපැල් තහනම් කිරීම සඳහා බොට් හිමිකරුවන් විසින් භාවිතා කරනු ලැබේ. මෙය ආරක්ෂා කිරීමට උපකාරී වේ \
ඔබ සහ ඔබේ කණ්ඩායම් හැකි ඉක්මනින් අයාචිත තැපැල් ගංවතුර ඉවත් කිරීමෙන්. Call ඇමතීමෙන් ඒවා ඔබගේ කණ්ඩායම සඳහා අක්‍රිය කළ හැකිය
/gbanstat
"""

__mod_name__ = "Global Bans"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_STATUS = CommandHandler("gbanstat", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
