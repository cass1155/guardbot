# Telegram Moderation Bot

A powerful, inline-only Telegram moderation bot built with Aiogram 3, SQLAlchemy, and Redis.

## Features
- **Inline Admin Panel**: Manage everything via private messages with the bot.
- **Multi-Chat Support**: One admin can manage multiple chats.
- **Filters**: Regex, Links, CAPS, Keywords, etc.
- **Punishments**: Delete, Mute, Ban.
- **No Persistent Roles**: Admin rights are verified via Telegram API on every action.

## Setup

1. **Clone the repository**
2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
   - `BOT_TOKEN`: Get from @BotFather.
   - `POSTGRES_*`: Database credentials.
   - `REDIS_*`: Redis credentials.

3. **Run with Docker**
   ```bash
   docker-compose up --build -d
   ```

## Usage
1. Add the bot to your group as an **Administrator**.
2. Send `/start` to the bot in **Private Messages**.
3. Select the chat you want to manage from the inline menu.
4. Configure filters and settings.

## Development
- Install dependencies: `poetry install`
- Run locally: `python -m bot`
