#!/usr/bin/python3

import os
import time
import requests
import psycopg2
from psycopg2 import sql

TELEGRAM_TOKEN = os.getenv('MSGTELEGRAM_TOKEN')
TELEGRAM_CHATIDS = os.getenv('MSGTELEGRAM_CHATIDS')
if TELEGRAM_CHATIDS is not None and TELEGRAM_CHATIDS is not None:
    if ',' in TELEGRAM_CHATIDS:
        TELEGRAM_CHATIDS = TELEGRAM_CHATIDS.split(',')
    else:
        TELEGRAM_CHATIDS = [TELEGRAM_CHATIDS]
MSGWEBHOOK_URL = os.getenv('MSGWEBHOOK_URL')

conn = psycopg2.connect(
    dbname=os.getenv('POSTGRESQL_DB'),
    user=os.getenv('POSTGRESQL_USER'),
    password=os.getenv('POSTGRESQL_PASS'),
    host=os.getenv('POSTGRESQL_HOST')
)

notified_chat_ids = set()
print("Started Zammad Telegram Notifier")


def check_waiting_chats():
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM chat_sessions WHERE state = 'waiting'")
        waiting_chats = cur.fetchall()
        for chat in waiting_chats:
            if chat[0] not in notified_chat_ids:
                print(f"Found waiting chat with ID {chat[0]}.")
                notificationtext = f"There is a waiting chat with ID {chat[0]}."
                send_webhook_message(notificationtext)
                send_telegram_message(notificationtext)
                notified_chat_ids.add(chat[0])


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
            notificationtext = f"Chat with ID {chat_id} has been taken by {agent_name}."
            send_webhook_message(notificationtext)
            send_telegram_message(notificationtext)
            notified_chat_ids.remove(chat_id)


def send_telegram_message(message, disablenotification=False):
    if TELEGRAM_CHATIDS is not None and TELEGRAM_CHATIDS is not None:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/send_message"
        for chat_id in TELEGRAM_CHATIDS:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'disable_notification': disablenotification
            }
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print(f"Message sent to chat ID {chat_id}")
            else:
                print(f"Failed to send message to chat ID {chat_id}: {response.text}")
    else:
        print("No Telegram Chat IDs or Bot Token configured.")


def send_webhook_message(message, htmlmessage=None):
    if MSGWEBHOOK_URL is not None:
        if htmlmessage is None:
            htmlmessage = message
        payload = {
            "text": message,
            "html": htmlmessage,
            "msgtype": "m.text"
        }
        response = requests.post(MSGWEBHOOK_URL, data=payload)
        if 200 <= response.status_code < 300:
            print(f"Message sent to webhook.")
        else:
            print(f"Failed to send message to webhook: {response.status_code} {response.text}")
    else:
        print("No Webhook URL configured.")


def get_new_telegram_chats():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    if 'result' in data and len(data['result']) > 0:
        for chat in data['result']:
            chat_id = chat['message']['chat']['id']
            if chat_id and str(chat_id) not in TELEGRAM_CHATIDS:
                send_telegram_message(f"Your Telegram Chat ID is: {chat_id}", chat_id)


if __name__ == "__main__":
    get_new_telegram_chats()
    bootmessage = "Zammad Notifier started."
    send_webhook_message(bootmessage)
    send_telegram_message(bootmessage, disablenotification=True)
    while True:
        check_waiting_chats()
        check_started_chats()
        time.sleep(1)
