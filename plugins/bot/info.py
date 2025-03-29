import asyncio
import time
from typing import Optional, Union

from pyrogram import enums, filters
from ChampuMusic import app

# Define a dictionary to track the last message timestamp for each user
user_last_message_time = {}
user_command_count = {}
# Define the threshold for command spamming (e.g., 20 commands within 60 seconds)
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

# --------------------------------------------------------------------------------- #

INFO_TEXT = """**
❅─────✧❅✦❅✧─────❅
            ✦ ᴜsᴇʀ ɪɴғᴏ ✦

➻ ᴜsᴇʀ ɪᴅ ‣ **`{}`
**➻ ғɪʀsᴛ ɴᴀᴍᴇ ‣ **{}
**➻ ʟᴀsᴛ ɴᴀᴍᴇ ‣ **{}
**➻ ᴜsᴇʀɴᴀᴍᴇ ‣ **`{}`
**➻ ᴍᴇɴᴛɪᴏɴ ‣ **{}
**➻ ʟᴀsᴛ sᴇᴇɴ ‣ **{}
**➻ ᴅᴄ ɪᴅ ‣ **{}
**➻ ʙɪᴏ ‣ **`{}`

**❅─────✧❅✦❅✧─────❅**
"""

# --------------------------------------------------------------------------------- #

async def userstatus(user_id):
    try:
        user = await app.get_users(user_id)
        x = user.status
        if x == enums.UserStatus.RECENTLY:
            return "Recently."
        elif x == enums.UserStatus.LAST_WEEK:
            return "Last week."
        elif x == enums.UserStatus.LONG_AGO:
            return "Long time ago."
        elif x == enums.UserStatus.OFFLINE:
            return "Offline."
        elif x == enums.UserStatus.ONLINE:
            return "Online."
    except:
        return "**sᴏᴍᴇᴛʜɪɴɢ ᴡʀᴏɴɢ ʜᴀᴘᴘᴇɴᴇᴅ !**"

# --------------------------------------------------------------------------------- #

@app.on_message(
    filters.command(
        ["info", "userinfo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]
    )
)
async def userinfo(_, message):
    user_id = message.from_user.id
    current_time = time.time()
    
    # Anti-spam check
    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    chat_id = message.chat.id
    user_id = message.from_user.id

    if not message.reply_to_message and len(message.command) == 2:
        try:
            user_id = message.text.split(None, 1)[1]
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
        except Exception as e:
            return await message.reply_text(str(e))

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        try:
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
        except Exception as e:
            return await message.reply_text(str(e))

    else:
        try:
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
        except Exception as e:
            return await message.reply_text(str(e))

    status = await userstatus(user.id)
    id = user_info.id
    dc_id = user.dc_id
    first_name = user_info.first_name
    last_name = user_info.last_name if user_info.last_name else "No last name"
    username = user_info.username if user_info.username else "No Username"
    mention = user.mention
    bio = user_info.bio if user_info.bio else "No bio set"

    # Send user information as text (without any image)
    await app.send_message(
        chat_id,
        text=INFO_TEXT.format(id, first_name, last_name, username, mention, status, dc_id, bio),
        reply_to_message_id=message.id,
    )

__MODULE__ = "Usᴇʀ Iɴғᴏ"
__HELP__ = """
/ɪɴғᴏ [ᴜsᴇʀ_ɪᴅ]: Gᴇᴛ ᴅᴇᴛᴀɪʟᴇᴅ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴀ ᴜsᴇʀ.
/ᴜsᴇʀɪɴғᴏ [ᴜsᴇʀ_ɪᴅ]: Aʟɪᴀs ғᴏʀ /ɪɴғᴏ.
"""
