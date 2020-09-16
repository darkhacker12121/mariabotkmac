import html
import json
import random
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters

RUN_STRINGS = (
    "ඔයා කොහෙද යන්නේ කියලා ඔයා හිතන්නේ?",
    "හහ්? කුමක්? ඔවුන් පැන ගියාද?",
    "ZZzzZZzz... හහ්? කුමක්? ඔහ්, ඔවුන් නැවත වරක්, කමක් නැහැ.",
    "නැවත මෙහි එන්න!",
    "එතරම් වේගවත් නොවේ ...",
    "බිත්තිය දෙස බලන්න!",
    "මාව ඔවුන් සමඟ තනි නොකරන්න !!",
    "ඔයා දුවනවා, ඔයා මැරෙනවා.",
    "ඔබට විහිළු, මම සෑම තැනකම සිටිමි",
    "ඔයා ඒ ගැන පසුතැවෙනවා ...",
    "ඔබටත් උත්සාහ කරන්න / පයින් ගහන්න, මට ඇහෙනවා ඒක විනෝදයක් කියලා.",
    "වෙනත් කෙනෙකුට කරදර කරන්න, මෙහි කිසිවෙකු ගණන් ගන්නේ නැත.",
    "ඔබට දුවන්න පුළුවන්, නමුත් ඔබට සැඟවිය නොහැක.",
    "ඔබට ලැබී ඇත්තේ එපමණක්ද?",
    "මම ඔබ පිටුපසින් ...",
    "ඔබට සමාගමක් ඇත!",
    "අපට මෙය පහසුම ක්‍රමය හෝ දුෂ්කර ක්‍රමය කළ හැකිය.",
    "ඔබට එය තේරෙන්නේ නැහැ නේද?",
    "ඔව්, ඔබ දුවනවා නම් හොඳයි!",
    "කරුණාකර, මට කොතරම් සැලකිල්ලක් දක්වනවාදැයි මට මතක් කරන්න?",
    "මම ඔයා නම් මම වේගයෙන් දුවනවා.",
    "එය නියත වශයෙන්ම අප සොයන ඩ්‍රොයිඩ් ය.",
    "අවාසි ඔබට වාසිදායක වේවා.",
    "ප්රසිද්ධ අවසන් වදන්.",
    "ඔවුන් සදහටම අතුරුදහන් විය.",
    "\"ඔහ්, මා දෙස බලන්න! මම හරිම සිසිල්, මට බෝට්ටුවකින් දුවන්න පුළුවන්!\" - මෙම පුද්ගලයා",
    "ඔව් ඔව්, තට්ටු කරන්න /kickme දැනටමත්.",
    "මෙන්න, මෙම මුද්ද රැගෙන මොර්ඩෝර් වෙත යන්න.",
    "පුරාවෘත්තයට එය තිබේ, ඔවුන් තවමත් ධාවනය වේ ...",
    "හැරී පොටර් මෙන් නොව, ඔබේ දෙමාපියන්ට මා වෙතින් ඔබව ආරක්ෂා කළ නොහැක.",
    "බිය කෝපයට හේතු වේ. කෝපය වෛරයට තුඩු දෙයි. වෛරය දුක් වේදනා ඇති කරයි. ඔබ දිගටම බියෙන් දුවන්නේ නම්, සමහර විට "
    "ඊළඟ වෑඩර් වෙන්න.",
    "බහුවිධ ගණනය කිරීම් පසුව, ඔබේ ෂෙනානිගන් පිළිබඳ මගේ උනන්දුව හරියටම 0 බව මම තීරණය කර ඇත්තෙමි.",
    "පුරාවෘත්තයට එය තිබේ, ඒවා තවමත් ක්‍රියාත්මකයි.",
    "එය දිගටම කරගෙන යන්න, කෙසේ හෝ අපට ඔබව මෙහි අවශ්‍ය බව විශ්වාස නැත.",
    "ඔයා විශාරදයෙක්- ඔහ්. ඉන්න. ඔබ හැරී නොවේ, දිගටම ඉදිරියට යන්න.",
    "හල්වේ වල ධාවනය නොවේ!",
    "හස්ටා ලා විස්ටා, බබා.",
    "බල්ලන්ට එළියට දුන්නේ කවුද?",
    "එය විහිළුවක්, මන්ද කිසිවෙකු ගණන් නොගන්නා බැවිනි.",
    "අහ්, මොනතරම් නාස්තියක්ද? මම ඒකට කැමතියි.",
    "අවංකවම, මගේ ආදරණීය, මම නරකක් දෙන්නේ නැහැ.",
    "ඔබට සත්‍යය හසුරුවා ගත නොහැක!",
    "බොහෝ කලකට පෙර, මන්දාකිනියක බොහෝ away තින් ... කවුරුහරි ඒ ගැන සැලකිලිමත් වනු ඇත. තවදුරටත් නැත.",
    "හේයි, ඔවුන් දෙස බලන්න! ඔවුන් දුවන්නේ නොවැලැක්විය හැකි බැන්හම්මර් වලින් ... හුරුබුහුටි.",
    "හැන් මුලින්ම වෙඩි තැබුවා. මමත් එහෙමයි.",
    "සුදු හාවෙකු ඔබ පසුපස දුවන්නේ කුමක් ද?",
    "ඩොක්ටර් කියන විදියට ... දුවන්න!",
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} in the face with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
    "{user1} gave a friendly push to help {user2} learn to swim in lava."
)

ITEMS = (
    "cast iron skillet",
    "large trout",
    "baseball bat",
    "cricket bat",
    "wooden cane",
    "nail",
    "printer",
    "shovel",
    "CRT monitor",
    "physics textbook",
    "toaster",
    "portrait of Richard Stallman",
    "television",
    "five ton truck",
    "roll of duct tape",
    "book",
    "laptop",
    "old television",
    "sack of rocks",
    "rainbow trout",
    "rubber chicken",
    "spiked bat",
    "fire extinguisher",
    "heavy rock",
    "chunk of dirt",
    "beehive",
    "piece of rotten meat",
    "bear",
    "ton of bricks",
)

THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "bashes",
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


@run_async
def runs(bot: Bot, update: Update):
    update.effective_message.reply_text(random.choice(RUN_STRINGS))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ අවශ්‍ය නම් ssh කිරීමට හැකි වන පරිදි බොට්ගේ IP ලිපිනය යවයි.
        හිමිකරු පමණි.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "මුල් යවන්නා, {}, හැඳුනුම්පතක් ඇත`{}`.\nඉදිරියට යවන්නා, {}, හැඳුනුම්පතක් ඇත `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_text("{} id එක `{}`.".format(escape_markdown(user.first_name), user.id),
                                                parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text("ඔබේ හැඳුනුම්පත `{}`.".format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("මෙම කණ්ඩායමේ හැඳුනුම්පත `{}`.".format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        msg.reply_text("මට මෙයින් පරිශීලකයෙකු උපුටා ගත නොහැක.")
        return

    else:
        return

    text = "<b>User info</b>:" \
           "\nID: <code>{}</code>" \
           "\nFirst Name: {}".format(user.id, html.escape(user.first_name))

    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))

    text += "\nPermanent user link: {}".format(mention_html(user.id, "link"))

    if user.id == OWNER_ID:
        text += "\n\nමෙම පුද්ගලයා මගේ හිමිකරු - මම ඔවුන්ට එරෙහිව කිසි විටෙකත් කිසිවක් නොකරමි!"
    else:
        if user.id in SUDO_USERS:
            text += "\nමෙම පුද්ගලයා මගේ සුඩෝ භාවිතා කරන්නෙකි!" \
                    "මගේ හිමිකරු තරම් බලවත් - එබැවින් එය නරඹන්න."
        else:
            if user.id in SUPPORT_USERS:
                text += "\nමෙම පුද්ගලයා මගේ සහායක පරිශීලකයෙකි!" \
                        "තරමක් සූඩෝ භාවිතා කරන්නෙකු නොවේ, නමුත් ඔබට සිතියමෙන් ඉවත් කළ හැකිය."

            if user.id in WHITELIST_USERS:
                text += "\nමෙම පුද්ගලයා සුදු ලැයිස්තු ගත කර ඇත!" \
                        "ඒ කියන්නේ මට තහනම් කරන්න අවසර නැහැ/kick ඔවුන්ට."

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def get_time(bot: Bot, update: Update, args: List[str]):
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        update.effective_message.reply_text("එහි සෑම විටම මට කාලයයි!")
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S on %A %d %B")
                update.message.reply_text("It's {} in {}".format(time_there, location))


@run_async
def echo(bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@run_async
def gdpr(bot: Bot, update: Update):
    update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text("ඔබගේ පුද්ගලික දත්ත මකා දමා ඇත.\n\nමෙය තහනම් නොවන බව සලකන්න"
                                        "ඔබ ඕනෑම කතාබස් වලින්, එය විදුලි පණිවුඩ දත්ත මිස මාරි දත්ත නොවේ."
                                        "Flooding, අනතුරු ඇඟවීම් සහ ග්බාන්ස් ද සංරක්ෂණය කර ඇත "
                                        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
                                        "මකාදැමීමේ අයිතිය අදාළ නොවන බව එහි පැහැදිලිව සඳහන් වේ "
                                        "\"මහජන යහපත උදෙසා ඉටු කරන ලද කාර්යයක කාර්ය සාධනය සඳහා\", පවතින ආකාරයට "
                                        "ඉහත දත්ත කැබලි සඳහා නඩුව.",
                                        parse_mode=ParseMode.MARKDOWN)


MARKDOWN_HELP = """
මාර්ක්ඩවුන් යනු විදුලි පණිවුඩ මඟින් සහාය දක්වන ඉතා ප්‍රබල හැඩතල ගැන්වීමේ මෙවලමකි. {} එය තහවුරු කර ගැනීම සඳහා වැඩි දියුණු කිරීම් කිහිපයක් ඇත\
සුරකින ලද පණිවිඩ නිවැරදිව විග්‍රහ කර ඇති අතර බොත්තම් සෑදීමට ඔබට ඉඩ සලසයි.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>:පරිශීලකයින්ට විදුලි පණිවුඩ ලබා ගැනීමට මෙය විශේෂ වැඩි දියුණු කිරීමකි \
ඒවායේ සලකුණු කිරීමේ බොත්තම්.<code>buttontext</code> බොත්තම මත දර්ශනය වන දේ වනු ඇත, සහ <code>සමහර url</code> \
විවෘත කරන ලද url එක වනු ඇත.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
මෙය එක් පේළියකට එක් බොත්තමක් වෙනුවට තනි පේළියක බොත්තම් දෙකක් නිර්මාණය කරයි.

ඔබේ පණිවිඩය බව මතක තබා ගන්න <b>MUST</b> බොත්තමක් හැර වෙනත් පෙළක් අඩංගු වේ!
""".format(dispatcher.bot.first_name)


@run_async
def markdown_help(bot: Bot, update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text("පහත පණිවිඩය මා වෙත යොමු කිරීමට උත්සාහ කරන්න, එවිට ඔබට පෙනෙනු ඇත!")
    update.effective_message.reply_text("/save test This is a markdown test. _italics_, *bold*, `code`, "
                                        "[URL](example.com) [button](buttonurl:github.com) "
                                        "[button2](buttonurl://google.com:same)")


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text("Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS]))

@run_async
def stickerid(bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text("Hello " +
                                            "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)
                                            + ", ඔබ පිළිතුරු දෙන ස්ටිකර් හැඳුනුම්පත :\n```" + 
                                            escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
                                            parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                            msg.from_user.id) + ", Please reply to sticker message to get id sticker",
                                            parse_mode=ParseMode.MARKDOWN)
@run_async
def getsticker(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                            msg.from_user.id) + ", කරුණාකර ඔබ පහත ඉල්ලූ ගොනුව පරීක්ෂා කරන්න."
                                            "\nකරුණාකර මෙම අංගය ely ානවන්තව භාවිතා කරන්න!",
                                            parse_mode=ParseMode.MARKDOWN)
        bot.sendChatAction(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
        bot.sendChatAction(chat_id, "upload_photo")
        bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))
        
    else:
        bot.sendChatAction(chat_id, "typing")
        update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                            msg.from_user.id) + ", ස්ටිකර් රූපය ලබා ගැනීමට කරුණාකර ස්ටිකර් පණිවිඩයට පිළිතුරු දෙන්න",
                                            parse_mode=ParseMode.MARKDOWN)

# /ip is for private use
__help__ = """
 - /id: වත්මන් කණ්ඩායම් හැඳුනුම්පත ලබා ගන්න. පණිවිඩයකට පිළිතුරු දීමෙන් භාවිතා කරන්නේ නම්, එම පරිශීලකයාගේ හැඳුනුම්පත ලබා ගනී.
 - /runs: අහඹු ලෙස පිළිතුරු පෙළකින් පිළිතුරු දෙන්න.
 - /slap: පරිශීලකයෙකුට කම්මුලට ගසන්න, නැතහොත් පිළිතුරක් නොමැති නම් කම්මුලට ගසන්න.😂
 - /time <place>: දී ඇති ස්ථානයේ දේශීය වේලාව ලබා දෙයි.
 - /info: පරිශීලකයෙකු පිළිබඳ තොරතුරු ලබා ගන්න.
 - /gdpr: ඔබේ තොරතුරු බොට් දත්ත ගබඩාවෙන් මකා දමයි. පුද්ගලික කතාබස් පමණි.
 - /markdownhelp: qවිදුලි පණිවුඩයේ සලකුණු කිරීම ක්‍රියාත්මක වන ආකාරය පිළිබඳ සාරාංශය - එය හැඳින්විය හැක්කේ පුද්ගලික කතාබස් වලින් පමණි.
 - /stickerid: ස්ටිකර් එකකට පිළිතුරු දී එහි ස්ටිකර් හැඳුනුම්පත ලබා ගන්න.
 - /getsticker: ස්ටිකරයකට පිළිතුරු දී එම ස්ටිකරය .png සහ image ලෙස ලබා ගන්න.
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

TIME_HANDLER = CommandHandler("time", get_time, pass_args=True)

RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)


dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
