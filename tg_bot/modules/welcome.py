import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_welcome_type
from tg_bot.modules.helper_funcs.string_handling import markdown_parser, \
    escape_invalid_curly_brackets
from tg_bot.modules.log_channel import loggable

VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'count', 'chatname', 'mention']

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


# do not async
def send(update, message, keyboard, backup_message):
    try:
        msg = update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    except IndexError:
        msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                  "\nසටහන: වත්මන් පණිවිඩය විය"
                                                                  "සලකුණු කිරීමේ ගැටළු හේතුවෙන් අවලංගුය. වෙන්න පුළුවන් "
                                                                  "පරිශීලකයාගේ නම නිසා."),
                                                  parse_mode=ParseMode.MARKDOWN)
    except KeyError:
        msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                  "\nසටහන: වත්මන් පණිවිඩය "
                                                                  "සමහර අස්ථානගත වී ඇති ගැටලුවක් හේතුවෙන් වලංගු නොවේ "
                                                                  "කැරලි වරහන්. කරුණාකර යාවත්කාලීන කරන්න"),
                                                  parse_mode=ParseMode.MARKDOWN)
    except BadRequest as excp:
        if excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nසටහන: වත්මන් පණිවිඩයේ වලංගු නොවන url එකක් ඇත"
                                                                      "එහි එක් බොත්තමක් තුළ. කරුණාකර යාවත්කාලීන කරන්න."),
                                                      parse_mode=ParseMode.MARKDOWN)
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nසටහන: වත්මන් පණිවිඩයේ බොත්තම් ඇත"
                                                                      "සහාය නොදක්වන url ප්‍රොටෝකෝල භාවිතා කරන්න"
                                                                      "telegram. කරුණාකර යාවත්කාලීන කරන්න."),
                                                      parse_mode=ParseMode.MARKDOWN)
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nසටහන: වත්මන් පණිවිඩයේ නරක url කිහිපයක් ඇත. "
                                                                      "කරුණාකර යාවත්කාලීන කරන්න."),
                                                      parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! got invalid url host errors")
        else:
            msg = update.effective_message.reply_text(markdown_parser(backup_message +
                                                                      "\nසටහන: යවන විට දෝෂයක් ඇතිවිය "
                                                                      "අභිරුචි පණිවිඩය. කරුණාකර යාවත්කාලීන කරන්න.),
                                                      parse_mode=ParseMode.MARKDOWN)
            LOGGER.exception()

    return msg


@run_async
@user_admin
@loggable
def del_joined(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        del_pref = sql.get_del_pref(chat.id)
        if del_pref:
            update.effective_message.reply_text("මම දැන් කතාබහට සම්බන්ධ වූ පරිශීලකයා මකා දැමිය යුතුය.")
        else:
            update.effective_message.reply_text("මම දැනට පැරණි සම්බන්ධිත පණිවිඩ මකා නොදමමි!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_del_joined(str(chat.id), True)
        update.effective_message.reply_text("පැරණි සම්බන්ධිත පණිවිඩ මකා දැමීමට මම උත්සාහ කරමි!")
        return "<b>{}:</b>" \
               "\n#CLEAN_SERVICE_MESSAGE" \
               "\n<b>Admin:</b> {}" \
               "\nසම්බන්ධ වීමට මකාදැමීම ටොගල් කර ඇත <code>ON</code>.".format(html.escape(chat.title),
                                                                         mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_del_joined(str(chat.id), False)
        update.effective_message.reply_text("පැරණි සම්බන්ධිත පණිවිඩ මම මකා නොදමමි.")
        return "<b>{}:</b>" \
               "\n#CLEAN_SERVICE_MESSAGE" \
               "\n<b>Admin:</b> {}" \
               "\nමකාදැමීමට ටොගල් කර ඇත <code>OFF</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("මට තේරෙනවා'on/yes' හෝ 'off/no' පමනි!")
        return ""


@run_async
def delete_join(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    join = update.effective_message.new_chat_members
    if can_delete(chat, bot.id):
        del_join = sql.get_del_pref(chat.id)
        if del_join:
            update.message.delete()

@run_async
def new_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    should_welc, cust_welcome, welc_type = sql.get_welc_pref(chat.id)
    if should_welc:
        sent = None
        new_members = update.effective_message.new_chat_members
        for new_mem in new_members:
            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text("මාස්ටර් නිවසේ සිටී, අපි මෙම සාදය ආරම්භ කරමු!")
                continue

            # Don't welcome yourself
            elif new_mem.id == bot.id:
                continue

            else:
                # If welcome message is media, send with appropriate function
                if welc_type != sql.Types.TEXT and welc_type != sql.Types.BUTTON_TEXT:
                    ENUM_FUNC_MAP[welc_type](chat.id, cust_welcome)
                    return
                # else, move on
                first_name = new_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if new_mem.last_name:
                        fullname = "{} {}".format(first_name, new_mem.last_name)
                    else:
                        fullname = first_name
                    count = chat.get_members_count()
                    mention = mention_markdown(new_mem.id, escape_markdown(first_name))
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(cust_welcome, VALID_WELCOME_FORMATTERS)
                    res = valid_format.format(first=escape_markdown(first_name),
                                              last=escape_markdown(new_mem.last_name or first_name),
                                              fullname=escape_markdown(fullname), username=username, mention=mention,
                                              count=count, chatname=escape_markdown(chat.title), id=new_mem.id)
                    buttons = sql.get_welc_buttons(chat.id)
                    keyb = build_keyboard(buttons)
                else:
                    res = sql.DEFAULT_WELCOME.format(first=first_name)
                    keyb = []

                keyboard = InlineKeyboardMarkup(keyb)

                sent = send(update, res, keyboard,
                            sql.DEFAULT_WELCOME.format(first=first_name))  # type: Optional[Message]
            delete_join(bot, update)

        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest as excp:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)


@run_async
def left_member(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    if should_goodbye:
        left_mem = update.effective_message.left_chat_member
        if left_mem:
            # Ignore bot being kicked
            if left_mem.id == bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text("RIP Master")
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = left_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_members_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(cust_goodbye, VALID_WELCOME_FORMATTERS)
                res = valid_format.format(first=escape_markdown(first_name),
                                          last=escape_markdown(left_mem.last_name or first_name),
                                          fullname=escape_markdown(fullname), username=username, mention=mention,
                                          count=count, chatname=escape_markdown(chat.title), id=left_mem.id)
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)
            delete_join(bot, update)


@run_async
@user_admin
def welcome(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    # if no args, show current replies.
    if len(args) == 0 or args[0].lower() == "noformat":
        noformat = args and args[0].lower() == "noformat"
        pref, welcome_m, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            "මෙම කතාබහට එය පිළිගැනීමේ සැකසුම සකසා ඇත: `{}`.\n*පිළිගැනීමේ පණිවිඩය"
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if welcome_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

        else:
            if noformat:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m)

            else:
                ENUM_FUNC_MAP[welcome_type](chat.id, welcome_m, parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text("I'll be polite!")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text("මම දුක් වෙමි, තවදුරටත් ආයුබෝවන් නොකියමි😥. ")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("මට තේරෙනවා'on/yes' හෝ 'off/no' පමනි!")


@run_async
@user_admin
def goodbye(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "මෙම කතාබහට එය සමුගැනීමේ සැකසුම සකසා ඇත: `{}`.\n*සමුගැනීමේ පණිවිඩය "
            "(not filling the {{}}) is:*".format(pref),
            parse_mode=ParseMode.MARKDOWN)

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text("මිනිස්සු පිටව යන විට මට කණගාටුයි!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("ඔවුන් යනවා😌.")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text("මම දුක් වෙමි, තවදුරටත් ආයුබෝවන් නොකියමි😥")


@run_async
@user_admin
@loggable
def set_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("ඔබ පිළිතුරු දිය යුත්තේ කුමක් ද යන්න සඳහන් කර නැත!")
        return ""

    sql.set_custom_welcome(chat.id, content or text, data_type, buttons)
    msg.reply_text("අභිරුචි පිළිගැනීමේ පණිවිඩය සාර්ථකව සකසන්න!")

    return "<b>{}:</b>" \
           "\n#SET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nSet the welcome message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def reset_welcome(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_welcome(chat.id, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text("පිළිගැනීමේ පණිවිඩය පෙරනිමියට සාර්ථකව යළි පිහිටුවන්න! ")
    return "<b>{}:</b>" \
           "\n#RESET_WELCOME" \
           "\n<b>Admin:</b> {}" \
           "\nReset the welcome message to default.".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def set_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("අභිරුචි සමුගැනීමේ පණිවිඩය සාර්ථකව සකසන්න!")
    return "<b>{}:</b>" \
           "\n#SET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nSet the goodbye message.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def reset_goodbye(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text("සුභ පැතුම් පණිවිඩය පෙරනිමියට සාර්ථකව යළි පිහිටුවන්න!")
    return "<b>{}:</b>" \
           "\n#RESET_GOODBYE" \
           "\n<b>Admin:</b> {}" \
           "\nReset the goodbye message.".format(html.escape(chat.title),
                                                 mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def clean_welcome(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text("මම දින දෙකක් පැරණි පිළිගැනීමේ පණිවිඩ මකා දැමිය යුතුයි.")
        else:
            update.effective_message.reply_text("මම දැනට පැරණි පිළිගැනීමේ පණිවිඩ මකා නොදමමි!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text("මම පැරණි පිළිගැනීමේ පණිවිඩ මකා දැමීමට උත්සාහ කරමි!")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>ON</code>.".format(html.escape(chat.title),
                                                                         mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text("I won't delete old welcome messages.")
        return "<b>{}:</b>" \
               "\n#CLEAN_WELCOME" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled clean welcomes to <code>OFF</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""


WELC_HELP_TXT = "ඔබගේ කණ්ඩායමේ පිළිගැනීමේ / සමුගැනීමේ පණිවිඩ විවිධ ආකාරවලින් පුද්ගලීකරණය කළ හැකිය. ඔබට පණිවිඩ අවශ්‍ය නම් " \
                " පෙරනිමි පිළිගැනීමේ පණිවිඩය මෙන් තනි තනිව ජනනය කිරීමට, ඔබට * මෙම * විචල්‍යයන් භාවිතා කළ හැකිය:\n" \
                " - `{{first}}`: මෙය පරිශීලකයා නියෝජනය කරයි *first* name\n" \
                " - `{{last}}`: මෙය පරිශීලකයා නියෝජනය කරයි *last* නාමය. පෙරනිමි *first name* පරිශීලකයාට නොමැති නම් " \
                "last name.\n" \
                " - `{{fullname}}`: මෙය පරිශීලකයා නියෝජනය කරයි *full* නාමය. පෙරනිමි *first name* පරිශීලකයාට නොමැති නම්" \
                "last name.\n" \
                " - `{{username}}`:  මෙය පරිශීලකයා නියෝජනය කරයි *username*. පෙරනිමි *mention* පරිශීලකයාට නොමැති නම්"\
                "first name if has no username.\n" \
                " - `{{mention}}`: මෙය සරලවම *mentions* පරිශීලකයෙක් -ඔවුන්ගේ මුල් නම සමඟ ටැග් කිරීම.\n" \
                " - `{{id}}`:මෙය පරිශීලකයා නියෝජනය කරයි *id*\n" \
                " - `{{count}}`:මෙය පරිශීලකයා නියෝජනය කරයි *member number*.\n" \
                " - `{{chatname}}`: මෙය පරිශීලකයා නියෝජනය කරයි *current chat name*.\n" \
                "\nසෑම විචල්යයක්ම වට කළ යුතුය`{{}}` ප්රතිස්ථාපනය කිරීමට.\n" \
                "පිළිගැනීමේ පණිවිඩ සලකුණු සලකුණු වලටද සහාය දක්වයි, එවිට ඔබට ඕනෑම අංගයක් සෑදිය හැකිය bold/italic/code/links. " \
                "බොත්තම් ද සහය දක්වයි, එබැවින් ඔබට හොඳ හැඳින්වීමක් සමඟින් ඔබේ පිළිගැනීම් නියමයි " \
                "buttons.\n" \
                "ඔබගේ නීති වලට සම්බන්ධ බොත්තමක් සෑදීමට, මෙය භාවිතා කරන්න: `[Rules](buttonurl://t.me/{}?start=group_id)`. " \
                "ලබා ගත හැකි ඔබේ කණ්ඩායමේ හැඳුනුම්පත සමඟ `group_id` වෙනුවට ආදේශ කරන්න via /id, ඔයා හොඳයි " \
                "යන්න. කණ්ඩායම් අයිඩී සාමාන්‍යයෙන් `-` ලකුණකට පෙර ඇති බව සලකන්න; මෙය අවශ්‍යයි, එබැවින් කරුණාකර එසේ නොකරන්න " \
                "remove it.\n" \
                "ඔබට විනෝදයක් දැනෙනවා නම්, ඔබට පවා සැකසිය හැකිය images/gifs/videos/voice විසින් පිළිගැනීමේ පණිවිඩය ලෙස පණිවිඩ" \
                "අපේක්ෂිත මාධ්‍යයට පිළිතුරු දීම සහ ඇමතීම /setwelcome.".format(dispatcher.bot.username)


@run_async
@user_admin
def welcome_help(bot: Bot, update: Update):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref, _, _ = sql.get_welc_pref(chat_id)
    goodbye_pref, _, _ = sql.get_gdbye_pref(chat_id)
    return "මෙම කතාබහට එය පිළිගැනීමේ මනාපය `ලෙස සකසා ඇත {}`.\n" \
           "එය සමුගැනීමේ මනාපයයි`{}`.".format(welcome_pref, goodbye_pref)


__help__ = """
{}

*පරිපාලක පමණි:*
 - /welcome <on/off>: enable/disable පණිවිඩ පිළිගන්න.
 - /welcome: වත්මන් පිළිගැනීමේ සැකසුම් පෙන්වයි.
 - /welcome noformat: ආකෘතිකරණයකින් තොරව වත්මන් පිළිගැනීමේ සැකසුම් පෙන්වයි - ඔබගේ පිළිගැනීමේ පණිවිඩ ප්‍රතිචක්‍රීකරණය කිරීමට ප්‍රයෝජනවත් වේ!
 - /goodbye -> එකම භාවිතය සහ තර්ක ලෙස /welcome.
 - /setwelcome <sometext>: අභිරුචි පිළිගැනීමේ පණිවිඩයක් සකසන්න. මාධ්‍යයට පිළිතුරු සැපයීම භාවිතා කරන්නේ නම්, එම මාධ්‍යය භාවිතා කරයි.
 - /setgoodbye <sometext>: අභිරුචි සමුගැනීමේ පණිවිඩයක් සකසන්න. මාධ්‍යයට පිළිතුරු සැපයීම භාවිතා කරන්නේ නම්, එම මාධ්‍යය භාවිතා කරයි.
 - /resetwelcome: සුපුරුදු පිළිගැනීමේ පණිවිඩයට යළි පිහිටුවන්න.
 - /resetgoodbye: සුපුරුදු සමුගැනීමේ පණිවිඩයට යළි පිහිටුවන්න.
 - /cleanwelcome <on/off>: නව සාමාජිකයෙකු මත, චැට් අයාචිත තැපැල් නොකිරීමට පෙර පිළිගැනීමේ පණිවිඩය මකා දැමීමට උත්සාහ කරන්න.
 - /clearjoin <on/off>: යමෙකු සම්බන්ධ වූ විට, කණ්ඩායම් පණිවිඩයට සම්බන්ධ වූ * පරිශීලකයා * මකා දැමීමට උත්සාහ කරන්න.
 - /welcomehelp: අභිරුචි සඳහා වැඩි ආකෘතිකරණ තොරතුරු බලන්න welcome/goodbye messages.

""".format(WELC_HELP_TXT)

__mod_name__ = "Welcomes/Goodbyes"

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
WELC_PREF_HANDLER = CommandHandler("welcome", welcome, pass_args=True, filters=Filters.group)
GOODBYE_PREF_HANDLER = CommandHandler("goodbye", goodbye, pass_args=True, filters=Filters.group)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_GOODBYE = CommandHandler("setgoodbye", set_goodbye, filters=Filters.group)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome, filters=Filters.group)
RESET_GOODBYE = CommandHandler("resetgoodbye", reset_goodbye, filters=Filters.group)
CLEAN_WELCOME = CommandHandler("cleanwelcome", clean_welcome, pass_args=True, filters=Filters.group)
DEL_JOINED = CommandHandler("clearjoin", del_joined, pass_args=True, filters=Filters.group)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)


dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(DEL_JOINED)
dispatcher.add_handler(WELCOME_HELP)
