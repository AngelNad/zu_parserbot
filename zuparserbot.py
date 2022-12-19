import os
import sqlite3

import pandas
from dotenv import load_dotenv
from telegram import ParseMode, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

load_dotenv()

secret_token = os.getenv('TOKEN')


def load_file(update, context):
    """Функция запрашивает файл определенного формата у пользователя."""
    chat = update.effective_chat
    # The file requests from the user
    context.bot.send_message(
        chat_id=chat.id,
        text='Отправьте, пожалуйста, мне файл excel в формате:\n'
             ' название товара, URL, xpath запрос.'
    )


def download(update, context):
    """Функция обработки файла от пользователя и сохранение в БД SQLite."""
    chat = update.effective_chat

    # The bot receives the file and saves
    with open('file.xlsx', 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)

    context.bot.send_message(
        chat_id=chat.id,
        text='Cпасибо, файл получен.\nЕго содержимое:'
    )

    # Opens the file with the Pandas library
    excel_data_df = pandas.read_excel('file.xlsx', sheet_name='Лист1')

    # Outputs the content in response to the user
    all_columns = ''
    values = ''
    for m in excel_data_df.columns:
        column = str(m)
        all_columns += column + ' '
    update.message.reply_text(
        f'\n<pre>{all_columns}</pre>',
        parse_mode=ParseMode.HTML
    )
    for n in excel_data_df.values:
        for i in n:
            value = str(i)
            values += value + ' '
        update.message.reply_text(
            f'\n<pre>{values}</pre>',
            parse_mode=ParseMode.HTML
        )
        values = ''

    # Save the content to the local db SQLite
    tup_excel_data_df = [tuple(val) for val in excel_data_df.values]
    conn = sqlite3.connect('parsing.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS product(
    productname TEXT, url TEXT, xpath TEXT
    );
    ''')
    cur.executemany(
        'INSERT INTO product VALUES(?, ?, ?);', tup_excel_data_df
    )
    conn.commit()


def wake_up(update, context):
    """Функция активизации бота по команде /start."""
    chat = update.effective_chat
    button = ReplyKeyboardMarkup([['Загрузить файл']], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text='Здесь вы можете загрузить файл с сайтами для парсинга',
        reply_markup=button,
    )


def main():
    """Уникальная функция, точка выполнения для файла программы."""
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, load_file))
    updater.dispatcher.add_handler(MessageHandler(Filters.document, download))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
