import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_mutes_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GMUTE
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GMUTE_ENFORCE_GROUP = 6


@run_async
def gmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("මම ඔත්තු බැලුවෙමි, මගේ කුඩා ඇසෙන් ... සුඩෝ පරිශීලක යුද්ධයක්! ඇයි ඔයාලා එකිනෙකාට හරවන්නේ?")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH යමෙක් ආධාරක පරිශීලකයෙකු මැඩපැවැත්වීමට උත්සාහ කරයි! *පොප්කෝන් අල්ලා ගනී😎😎*")
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
        message.reply_text("That's not a user!")
        return

    if sql.is_user_gmuted(user_id):
        if not reason:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් gmuted; මම හේතුව වෙනස් කරන්නම්, නමුත් ඔබ මට එකක් දුන්නේ නැහැ ...🥺🥺")
            return

        success = sql.update_gmute_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if success:
            message.reply_text("මෙම පරිශීලකයා දැනටමත් gmuted; මම ගොස් gmute හේතුව යාවත්කාලීන කර ඇත!")
        else:
            message.reply_text("නැවත උත්සාහ කිරීමට ඔබට අවශ්‍යද? මම හිතුවේ මේ පුද්ගලයා gmuted ඇති, නමුත් පසුව ඔවුන් එසේ නොවේ? "
                               "Am very confused")

        return

    message.reply_text("*ඩක් ටේප් සූදානම්* 😉")

    muter = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} is gmuting user {} "
                 "because:\n{}".format(mention_html(muter.id, muter.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or "කිසිදු හේතුවක් දක්වා නැත"),
                 html=True)

    sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            bot.restrict_chat_member(chat_id, user_id, can_send_messages=False)
        except BadRequest as excp:
            if excp.message == "පරිශීලකයා චැට් හි පරිපාලකයෙකි":
                pass
            elif excp.message == "චැට් හමු නොවීය":
                pass
            elif excp.message == "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා කිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත":
                pass
            elif excp.message == "සහභාගිවන්නා_භාවිතා_කරන්න":
                pass
            elif excp.message == "Peer_id_invalid":  # Suspect this happens when a group is suspended by telegram.
                pass
            elif excp.message == "කණ්ඩායම් කතාබහ අක්‍රිය කරන ලදි":
                pass
            elif excp.message == "මූලික කණ්ඩායමකින් එය පයින් ගැසීමට පරිශීලකයෙකුගේ ආරාධිතයා විය යුතුය":
                pass
            elif excp.message == "චැට්_පරිපාලක_අවශ්‍යයි":
                pass
            elif excp.message == "කණ්ඩායම් පරිපාලකයින්ට kick ගැසිය හැක්කේ මූලික කණ්ඩායමක නිර්මාතෘට පමණි":
                pass
            elif excp.message == "ක්‍රමය ලබා ගත හැක්කේ සුපිරි කණ්ඩායම් සඳහා පමණි":
                pass
            elif excp.message == "චැට් නිර්මාතෘ පහත් කළ නොහැක":
                pass
            else:
                message.reply_text("නිසා gmute කිරීමට නොහැකි විය: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "නිසා gmute කිරීමට නොහැකි විය: {}".format(excp.message))
                sql.ungmute_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "gmute complete!")
    message.reply_text("පුද්ගලයා gmute කර ඇත.")


@run_async
def ungmute(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ඔබ පරිශීලකයෙකු වෙත යොමු වන බවක් නොපෙනේ.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("එය පරිශීලකයෙකු නොවේ!")
        return

    if not sql.is_user_gmuted(user_id):
        message.reply_text("මෙම පරිශීලකයා gmuted නොවේ!")
        return

    muter = update.effective_user  # type: Optional[User]

    message.reply_text("මම ඉඩ දෙන්නම් {} ගෝලීයව නැවත කතා කරන්න.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "{} ඉවත් නොකළ පරිශීලකයෙකු ඇත {}".format(mention_html(muter.id, muter.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'restricted':
                bot.restrict_chat_member(chat_id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)

        except BadRequest as excp:
            if excp.message == "පරිශීලකයා චැට් හි පරිපාලකයෙකි":
                pass
            elif excp.message == "චැට් හමු නොවීය":
                pass
            elif excp.message == "චැට් සාමාජිකයාව සීමා කිරීමට / සීමා නොකිරීමට ප්‍රමාණවත් අයිතිවාසිකම් නොමැත":
                pass
            elif excp.message == "පරිශීලකයා_සහභාගී_නොවෙ":
                pass
            elif excp.message == "සුපිරි කණ්ඩායම් සහ නාලිකා කතාබස් සඳහා පමණක් ක්‍රමය තිබේ":
                pass
            elif excp.message == "චැට් එකේ නැහැ":
                pass
            elif excp.message == "නාලිකාව_පුද්ගලිකයි:
                pass
            elif excp.message == "චැට්_පරිපාලක_අවශ්‍යයි":
                pass
            else:
                message.reply_text("මේ නිසා ඉවත් කිරීමට නොහැකි විය: {}".format(excp.message))
                bot.send_message(OWNER_ID, "මේ නිසා ඉවත් කිරීමට නොහැකි විය: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungmute_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gmute complete!")

    message.reply_text("පුද්ගලයා නිරුපද්‍රිතව ඇත.")


@run_async
def gmutelist(bot: Bot, update: Update):
    muted_users = sql.get_gmute_list()

    if not muted_users:
        update.effective_message.reply_text("Gmuted භාවිතා කරන්නන් නොමැත! මම හිතුවට වඩා ඔයා කරුණාවන්තයි ...😊😘")
        return

    mutefile = 'Screw these guys.\n'
    for user in muted_users:
        mutefile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            mutefile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(mutefile)) as output:
        output.name = "gmutelist.txt"
        update.effective_message.reply_document(document=output, filename="gmutelist.txt",
                                                caption="දැනට gmuted භාවිතා කරන්නන්ගේ ලැයිස්තුව මෙන්න.")


def check_and_mute(bot, update, user_id, should_message=True):
    if sql.is_user_gmuted(user_id):
        bot.restrict_chat_member(update.effective_chat.id, user_id, can_send_messages=False)
        if should_message:
            update.effective_message.reply_text("This is a bad person, I'll silence them for you!")


@run_async
def enforce_gmute(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gmute.
    if sql.does_chat_gmute(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_mute(bot, update, user.id, should_message=True)
        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_mute(bot, update, mem.id, should_message=True)
        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_mute(bot, update, user.id, should_message=True)

@run_async
@user_admin
def gmutestat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("මම මෙම කණ්ඩායමේ gmutes සක්‍රීය කර ඇත. මෙය ඔබව ආරක්ෂා කිරීමට උපකාරී වේ "
                                                "අයාචිත තැපැල්, අප්‍රසන්න චරිත සහ අනිරුද් වෙතින්.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("මම මෙම කණ්ඩායමේ gmutes අක්‍රීය කර ඇත. GMutes ඔබේ පරිශීලකයින්ට බලපාන්නේ නැත"
                                                "තවදුරටත්. ඔබට අඩු ආරක්ෂාවක් ලැබෙනු ඇත!")
    else:
        update.effective_message.reply_text("පසුබිමක් තෝරා ගැනීමට මට තර්ක කිහිපයක් දෙන්න! on/off, yes/no!\n\n"
                                            "ඔබගේ වර්තමාන සැකසුම: {}\n"
                                            "සත්‍ය වූ විට, සිදුවන ඕනෑම විකාරයක් ඔබගේ කණ්ඩායම තුළ ද සිදුවනු ඇත. "
                                            "අසත්‍ය වූ විට, ඔවුන් එසේ නොකරනු ඇත"
                                            "spammers.".format(sql.does_chat_gmute(update.effective_chat.id)))


def __stats__():
    return "{} gmuted users.".format(sql.num_gmuted_users())


def __user_info__(user_id):
    is_gmuted = sql.is_user_gmuted(user_id)

    text = "Globally muted: <b>{}</b>"
    if is_gmuted:
        text = text.format("Yes")
        user = sql.get_gmuted_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gmutes*: `{}`.".format(sql.does_chat_gmute(chat_id))


__help__ = """
*පරිපාලක පමණි:*
 - /gbanstat <on/off/yes/no>:ඔබගේ කණ්ඩායමට ගෝලීය තහනමේ බලපෑම අක්‍රීය කරනු ඇත, නැතහොත් ඔබගේ වර්තමාන සැකසුම් නැවත ලබා දෙනු ඇත.
ගෝලීය තහනම ලෙසද හැඳින්වෙන ග්බාන්ස්, සියලුම කණ්ඩායම් හරහා අයාචිත තැපැල් තහනම් කිරීම සඳහා බොට් හිමිකරුවන් විසින් භාවිතා කරනු ලැබේ. මෙය ආරක්ෂා කිරීමට උපකාරී වේ \
ඔබ සහ ඔබේ කණ්ඩායම් හැකි ඉක්මනින් අයාචිත තැපැල් ගංවතුර ඉවත් කිරීමෙන්. Call ඇමතීමෙන් ඒවා ඔබගේ කණ්ඩායම සඳහා අක්‍රිය කළ හැකිය
/gbanstat
"""

__mod_name__ = "Global Mute"

GMUTE_HANDLER = CommandHandler("gmute", gmute, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGMUTE_HANDLER = CommandHandler("ungmute", ungmute, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GMUTE_LIST = CommandHandler("gmutelist", gmutelist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GMUTE_STATUS = CommandHandler("gmutestat", gmutestat, pass_args=True, filters=Filters.group)

GMUTE_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gmute)

dispatcher.add_handler(GMUTE_HANDLER)
dispatcher.add_handler(UNGMUTE_HANDLER)
dispatcher.add_handler(GMUTE_LIST)
dispatcher.add_handler(GMUTE_STATUS)

if STRICT_GMUTE:
    dispatcher.add_handler(GMUTE_ENFORCER, GMUTE_ENFORCE_GROUP)
