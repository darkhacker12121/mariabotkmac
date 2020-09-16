import re
from io import BytesIO
from typing import Optional, List

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, RegexHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import dispatcher, MESSAGE_DUMP, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_note_type

from tg_bot.modules.connection import connected

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
def get(bot, update, notename, show_none=True, no_format=False):
    chat_id = update.effective_chat.id
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        send_id = user.id
    else:
        chat_id = update.effective_chat.id
        send_id = chat_id

    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=MESSAGE_DUMP, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "ඉදිරියට යැවීමේ පණිවිඩය හමු නොවීය":
                        message.reply_text("Tඔහුගේ පණිවිඩය නැති වී ඇති බව පෙනේ - මම එය ඉවත් කරමි"
                                           "ඔබගේ සටහන් ලැයිස්තුවෙන්.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "ඉදිරියට යැවීමේ පණිවිඩය හමු නොවීය":
                        message.reply_text("මෙම සටහනේ මුල් යවන්නා මකා දමා ඇති බව පෙනේ"
                                           "ඔවුන්ගේ පණිවිඩය - සමාවෙන්න! භාවිතා කිරීම ආරම්භ කිරීමට ඔබේ බොට් පරිපාලක ලබා ගන්න "
                                           "මෙය වළක්වා ගැනීම සඳහා පණිවිඩ ඩම්ප් කරන්න. මම මෙම සටහන ඉවත් කරමි "
                                           "ඔබගේ සුරකින ලද සටහන්.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            text = note.value
            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            should_preview_disabled = True
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)
                if "telegra.ph" in text or "youtu.be" in text:
                    should_preview_disabled = False

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(chat_id, text, reply_to_message_id=reply_id,
                                     parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                     reply_markup=keyboard)
                else:
                    ENUM_FUNC_MAP[note.msgtype](chat_id, note.file, caption=text, reply_to_message_id=reply_id,
                                                parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                                reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "ආයතනය_සඳහන්_කිරීම_පරිශීලකයා_අවලංගුය":
                    message.reply_text("මම මීට පෙර කවදාවත් දැක නැති කෙනෙකු ගැන සඳහන් කිරීමට ඔබ උත්සාහ කළ බවක් පෙනේ. ඔබ ඇත්තටම නම් "
                                       "ඒවා සඳහන් කිරීමට අවශ්‍යයි, ඔවුන්ගේ පණිවිඩයක් මා වෙත යොමු කරන්න, එවිට මට හැකි වනු ඇත"
                                       "ඒවා ටැග් කිරීමට!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text("මෙම සටහන වෙනත් බොට් එකකින් වැරදි ලෙස ආනයනය කරන ලද ගොනුවකි - මට භාවිතා කළ නොහැක "
                                       "එය. ඔබට එය සැබවින්ම අවශ්‍ය නම්, ඔබට එය නැවත සුරැකීමට සිදුවේ. තුළ "
                                       "මේ අතර, මම එය ඔබගේ සටහන් ලැයිස්තුවෙන් ඉවත් කරමි.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text("මෙම සටහන වැරදි ලෙස සංයුති කර ඇති බැවින් එය යැවිය නොහැක. ඇතුලට අහන්න"
                                       "@cyberwordk ඇයි කියලා හිතාගන්න බැරි නම්!")
                    LOGGER.exception("පණිවිඩය විග්‍රහ කිරීමට නොහැකි විය #%s කතාබස් කරමින් %s", notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("මෙම සටහන නොපවතී")


@run_async
def cmd_get(bot: Bot, update: Update, args: List[str]):
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(bot, update, args[0], show_none=True, no_format=True)
    elif len(args) >= 1:
        get(bot, update, args[0], show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
def hash_get(bot: Bot, update: Update):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(bot, update, no_hash, show_none=False)


@run_async
@user_admin
def save(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)

    if data_type is None:
        msg.reply_text("Dude, there's no note")
        return

    if len(text.strip()) == 0:
        text = note_name

    sql.add_note_to_db(chat_id, note_name, text, data_type, buttons=buttons, file=content)

    msg.reply_text(
        "හරි, එකතු කළා {note_name} in *{chat_name}*.\nGet it with /get {note_name}, or #{note_name}".format(note_name=note_name, chat_name=chat_name), parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text("ඔබ බොට් එකකින් පණිවිඩයක් සුරැකීමට උත්සාහ කරන බවක් පෙනේ. අවාසනාවට, "
                           "බොට්ස් වලට බොට් පණිවිඩ යැවිය නොහැක, එබැවින් මට නිශ්චිත පණිවිඩය සුරැකිය නොහැක. "
                           "\nමට හැකි සියලුම පෙළ මම සුරකිමි, නමුත් ඔබට තවත් අවශ්‍ය නම් ඔබට එය කිරීමට සිදුවේ "
                           "පණිවිඩය ඔබම යොමු කර එය සුරකින්න.")
        else:
            msg.reply_text("බොට්ස් ටෙලිග්‍රාම් මගින් තරමක් ආබාධිත වන අතර එය බොට් කිරීමට අපහසු වේ"
                           "වෙනත් බොට්ස් සමඟ අන්තර් ක්‍රියා කරන්න, එවිට මට මෙම පණිවිඩය සුරැකිය නොහැක "
                           "මම සාමාන්‍යයෙන් කැමතියි - ඔබට එය ඉදිරිපත් කිරීමට අවශ්‍යද?"
                           "එහෙනම් ඒ නව පණිවිඩය සුරකිනවාද? ස්තූතියි!")
        return


@run_async
@user_admin
def clear(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("සටහන සාර්ථකව ඉවත් කරන ලදි.")
        else:
            update.effective_message.reply_text("එය මගේ දත්ත ගබඩාවේ සටහනක් නොවේ!")


@run_async
def list_notes(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        msg = "*Notes in {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = ""
            msg = "*Local Notes:*\n"
        else:
            chat_name = chat.title
            msg = "*Notes in {}:*\n"

    note_list = sql.get_all_chat_notes(chat_id)

    for note in note_list:
        note_name = escape_markdown(" - {}\n".format(note.name))
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == "*Notes in chat:*\n":
        update.effective_message.reply_text("No notes in this chat!")

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(chat_id, document=output, filename="failed_imports.txt",
                                         caption="මේ files/photos ආරම්භය හේතුවෙන් ආනයනය කිරීමට අපොහොසත් විය "
                                                 "වෙනත් බෝට්ටුවකින්. මෙය විදුලි පණිවුඩ API සීමා කිරීමක් වන අතර එය කළ නොහැක "
                                                 "වළක්වා ගත යුතුය. අපහසුතාවයට කනගාටුයි!")


def __stats__():
    return "{} notes, across {} chats.".format(sql.num_notes(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return "There are `{}` notes in this chat.".format(len(notes))


__help__ = """
 - /get <notename>: මෙම සටහන් නාමය සමඟ සටහන ලබා ගන්න
 - #<notename>: same as /get
 - /notes or /saved:මෙම සංවාදයේ සුරකින ලද සියලුම සටහන් ලැයිස්තුගත කරන්න

සටහනක අන්තර්ගතය කිසිදු හැඩතල ගැන්වීමකින් තොරව ලබා ගැනීමට ඔබ කැමති නම්, භාවිතා කරන්න`/get <notename> noformat`.මෙය කළ හැකිය \
වත්මන් සටහනක් යාවත්කාලීන කිරීමේදී ප්‍රයෝජනවත් වන්න.

*පරිපාලක පමණි:*
 - /save <notename> <notedata>:සටහන් නාම නාමයක් සහිත සටහනක් ලෙස සටහන් කිරීම සුරකිනු ඇත
සම්මත සලකුණු සම්බන්ධක සින්ටැක්ස් භාවිතා කිරීමෙන් සටහනකට බොත්තමක් එක් කළ හැකිය - සබැඳිය a සමඟ පෙර සූදානම් කළ යුතුය\
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check /markdownhelp වැඩි විස්තර සඳහා.
 - /save <notename>: පිළිතුරු දුන් පණිවිඩය නාම නාමයක් සහිත සටහනක් ලෙස සුරකින්න
 - /clear <notename>: මෙම නම සහිත පැහැදිලි සටහනක්
"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
HASH_GET_HANDLER = RegexHandler(r"^#[^\s]+", hash_get)

SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"], list_notes, admin_ok=True)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
