from pyrogram import filters
from pymongo import MongoClient
from ChampuMusic import app
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)
from pyrogram.types import InputMediaPhoto
from typing import Union
import asyncio
import random
import requests
import os
import time
from pyrogram.enums import ChatType
import config
import matplotlib.pyplot as plt
import io

# MongoDB connection
mongo_client = MongoClient(config.MONGO_DB_URI)
db = mongo_client["Rankings"]
collection = db["ranking"]
daily_collection = db["daily_ranking"]

# In-memory data storage
user_data = {}
today = {}

# Load daily rankings from MongoDB on bot start
async def load_daily_rankings():
    global today
    today = {}
    for chat in daily_collection.find():
        chat_id = chat["_id"]
        today[chat_id] = chat["users"]

# Function to generate a bar chart for rankings
def generate_ranking_chart(data, title):
    users = [entry[0] for entry in data]
    messages = [entry[1] for entry in data]

    plt.figure(figsize=(10, 6))
    plt.bar(users, messages, color='skyblue')
    plt.xlabel('Users')
    plt.ylabel('Total Messages')
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# Watcher for today's messages
@app.on_message(filters.group & filters.group, group=6)
def today_watcher(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id in today and user_id in today[chat_id]:
        today[chat_id][user_id]["total_messages"] += 1
    else:
        if chat_id not in today:
            today[chat_id] = {}
        if user_id not in today[chat_id]:
            today[chat_id][user_id] = {"total_messages": 1}
        else:
            today[chat_id][user_id]["total_messages"] = 1
    
    # Save to MongoDB
    daily_collection.update_one(
        {"_id": chat_id},
        {"$set": {"users": today[chat_id]}},
        upsert=True
    )

# Watcher for overall messages
@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    user_id = message.from_user.id    
    user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
    user_data[user_id]["total_messages"] += 1    
    collection.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)

# Command to display today's leaderboard
@app.on_message(filters.command("today"))
async def today_(_, message):
    chat_id = message.chat.id
    if chat_id in today:
        users_data = [(user_id, user_data["total_messages"]) for user_id, user_data in today[chat_id].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            total_messages_count = sum(user_data['total_messages'] for user_data in today[chat_id].values())
               
            response = f"⬤ 📈 ᴛᴏᴅᴀʏ ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages_count}\n\n"

            for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info

            # Generate chart
            chart_data = [(await app.get_users(user_id)).first_name if (await app.get_users(user_id)).first_name else "Unknown" for user_id, _ in sorted_users_data]
            chart_values = [total_messages for _, total_messages in sorted_users_data]
            chart = generate_ranking_chart(list(zip(chart_data, chart_values)), "Today's Leaderboard")

            button = InlineKeyboardMarkup(
                [[    
                   InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="overall"),
                ]])
            await message.reply_photo(chart, caption=response, reply_markup=button, has_spoiler=True)
        else:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
    else:
        await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")

# Command to display overall leaderboard
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    top_members = collection.find().sort("total_messages", -1).limit(10)

    response = "⬤ 📈 ᴄᴜʀʀᴇɴᴛ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
    chart_data = []
    chart_values = []
    for idx, member in enumerate(top_members, start=1):
        user_id = member["_id"]
        total_messages = member["total_messages"]
        try:
            user_name = (await app.get_users(user_id)).first_name
        except:
            user_name = "Unknown"

        user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
        response += user_info
        chart_data.append(user_name)
        chart_values.append(total_messages)

    # Generate chart
    chart = generate_ranking_chart(list(zip(chart_data, chart_values)), "Overall Leaderboard")

    button = InlineKeyboardMarkup(
            [[    
               InlineKeyboardButton("ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="today"),
            ]])
    await message.reply_photo(chart, caption=response, reply_markup=button, has_spoiler=True)

# Callback query for today's leaderboard
@app.on_callback_query(filters.regex("today"))
async def today_rank(_, query):
    chat_id = query.message.chat.id
    if chat_id in today:
        users_data = [(user_id, user_data["total_messages"]) for user_id, user_data in today[chat_id].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            response = "⬤ 📈 ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
            for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info

            # Generate chart
            chart_data = [(await app.get_users(user_id)).first_name if (await app.get_users(user_id)).first_name else "Unknown" for user_id, _ in sorted_users_data]
            chart_values = [total_messages for _, total_messages in sorted_users_data]
            chart = generate_ranking_chart(list(zip(chart_data, chart_values)), "Today's Leaderboard")

            button = InlineKeyboardMarkup(
                [[    
                   InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="overall"),
                ]])
            await query.message.edit_media(InputMediaPhoto(chart, caption=response), reply_markup=button)
        else:
            await query.answer("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
    else:
        await query.answer("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")

# Callback query for overall leaderboard
@app.on_callback_query(filters.regex("overall"))
async def overall_rank(_, query):
    top_members = collection.find().sort("total_messages", -1).limit(10)

    response = "⬤ 📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
    chart_data = []
    chart_values = []
    for idx, member in enumerate(top_members, start=1):
        user_id = member["_id"]
        total_messages = member["total_messages"]
        try:
            user_name = (await app.get_users(user_id)).first_name
        except:
            user_name = "Unknown"

        user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
        response += user_info
        chart_data.append(user_name)
        chart_values.append(total_messages)

    # Generate chart
    chart = generate_ranking_chart(list(zip(chart_data, chart_values)), "Overall Leaderboard")

    button = InlineKeyboardMarkup(
            [[    
               InlineKeyboardButton("ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="today"),
            ]])
    await query.message.edit_media(InputMediaPhoto(chart, caption=response), reply_markup=button)

# Load daily rankings when the bot starts
app.run(load_daily_rankings())