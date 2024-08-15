#!/usr/bin/python3

import os
import time
import requests
import psycopg2
from psycopg2 import sql

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_IDS = os.getenv('CHAT_IDS')
if ',' in CHAT_IDS:
    CHAT_IDS = CHAT_IDS.split(',')
else:
    CHAT_IDS = [CHAT_IDS]

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST')
)

notified_chat_ids = set()
print("Started Zammad Telegram Notification Service")

def check_waiting_chats():
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM chat_sessions WHERE state = 'waiting'")
        waiting_chats = cur.fetchall()
        for chat in waiting_chats:
            chat_id = chat[0]
            if chat_id not in notified_chat_ids:
                print(f"Found waiting chat with ID {chat_id}.")
                for telegram_chat_id in CHAT_IDS:
                    send_telegram_message(f"There is a waiting chat with ID {chat_id}.", telegram_chat_id)
                notified_chat_ids.add(chat_id)

def check_started_chats():
    with conn.cursor() as cur:
        cur.execute("""
            SELECT cs.id, u.firstname, u.lastname
            FROM chat_sessions cs
            JOIN users u ON cs.user_id = u.id
            WHERE cs.state = 'running' AND cs.id = ANY(%s)
        """, (list(notified_chat_ids),))
        started_chats = cur.fetchall()
        for chat in started_chats:
            chat_id, firstname, lastname = chat
            agent_name = f"{firstname} {lastname}"
            print(f"Chat with ID {chat_id} started by agent {agent_name}.")
            for telegram_chat_id in CHAT_IDS:
                send_telegram_message(f"Chat with ID {chat_id} has been taken by {agent_name}.", telegram_chat_id)
            notified_chat_ids.remove(chat_id)

def send_telegram_message(message, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"Message sent to chat ID {chat_id}")
    else:
        print(f"Failed to send message to chat ID {chat_id}: {response.text}")

def get_chat_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    if 'result' in data and len(data['result']) > 0:
        chat_id = data['result'][0]['message']['chat']['id']
        return chat_id
    return None

if __name__ == "__main__":
    chat_id = get_chat_id()
    if chat_id and str(chat_id) not in CHAT_IDS:
        send_telegram_message(f"Your Chat ID is: {chat_id}", chat_id)

    for chat_id in CHAT_IDS:
        send_telegram_message("Zammad Telegram Notification Service started.", chat_id)
    
    while True:
        check_waiting_chats()
        check_started_chats()
        time.sleep(1)
