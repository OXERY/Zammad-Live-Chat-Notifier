# Zammad Live-Chat Telegram Notifier

This Python script monitors Zammad for new livechat sessions. The docker compose based Zammad setup is currently required to make this setup work.

When a new live-chat request is registered, configured Telegram Chat-IDs will be notified.
Another notification is sent, when a Zammad user has taken the Chat, so other agents do not have to take a look.

## Prerequisites

- Docker compose based Zammad installation
- Telegram Bot Token


## Installation

1. Extend your Zammad's `docker-compose.override.yml` file with the additional _notifier_ container.

2. In the docker-compose.override.yml file, example values for the environment variables are provided for zammad's database.
Additionally, the Telegram Bot Token and Chat IDs have to be set in the compose or .env - as you prefer.

3. Execute the build and run the script:
```bash
docker-compose build notifier
docker-compose up -d notifier
```

## Running

The script will run in the background and check for new live-chat sessions every second.
Only during start of the container, it will check for new Telegram chat IDs and will send them their respective Chat ID.
No further communication happens to unconfigured Telegram Chat IDs.

To add a new Telegram Chat to it, send a message to the bot and restart the script. Afterwards, your new Telegram session receives a message with its Chat ID, which has to be configured in the compose or .env. Then, restart the container et voila.