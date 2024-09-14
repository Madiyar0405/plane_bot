import json
import logging
from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters


load_dotenv()
TOKEN = os.getenv('TOKEN')

try:
    with open('educational_programs.json', 'r', encoding='utf-8') as f:
        PROGRAMS_DATA = json.load(f)
        print("JSON файл успешно прочитан!")
except FileNotFoundError:
    print("Ошибка: Файл educational_programs.json не найден!")

CHOOSE_EDUCATION_LEVEL, CHOOSE_SEARCH_METHOD, SHOW_PROGRAMS = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет приветственное сообщение и предлагает выбрать уровень образования."""
    text = "👋 *Привет!* \n\nЭтот бот поможет вам найти информацию " \
           "об образовательных программах в Казахстане. \n\n" \
           "🔎 *Выберите уровень образования:*\n" \
           "/bachelor - Бакалавриат\n" \
           "/master - Магистратура\n" \
           "/doctorate - Докторантура"
    await update.message.reply_text(text, parse_mode='Markdown')
    return CHOOSE_EDUCATION_LEVEL

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображает список доступных команд."""
    text = "📚 *Доступные команды:*\n\n" \
           "/start - Начать работу с ботом\n" \
           "/help - Показать список команд\n" \
           "/bachelor - Выбрать уровень образования 'Бакалавриат'\n" \
           "/master - Выбрать уровень образования 'Магистратура'\n" \
           "/doctorate - Выбрать уровень образования 'Докторантура'\n" \
           "/by_university - Искать программу по названию вуза\n" \
           "/by_specialty - Искать программу по специальности"
    await update.message.reply_text(text, parse_mode='Markdown')


async def choose_education_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор уровня образования и предлагает выбрать способ поиска."""
    user_data = context.user_data
    user_data['education_level'] = update.message.text[1:]  
    text = "🔍 *Выберите способ поиска:*\n" \
           "/by_university - По названию вуза\n" \
           "/by_specialty - По специальности"
    await update.message.reply_text(text, parse_mode='Markdown')
    return CHOOSE_SEARCH_METHOD

async def choose_search_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор способа поиска."""
    user_data = context.user_data
    user_data['search_method'] = update.message.text[1:] 

    if user_data['search_method'] == 'by_university':
        universities = sorted(set(program['name'] for program in PROGRAMS_DATA))
        text = "🏢 *Выберите ВУЗ:*\n" + "\n".join(f"/{i} - {uni}" for i, uni in enumerate(universities))
        await update.message.reply_text(text, parse_mode='Markdown')
    elif user_data['search_method'] == 'by_specialty':
        text = "📝 *Введите ключевые слова для поиска специальности:*"
        await update.message.reply_text(text, parse_mode='Markdown')
    return SHOW_PROGRAMS

async def show_programs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает результаты поиска."""
    user_data = context.user_data
    education_level = user_data['education_level']
    search_method = user_data['search_method']

    if search_method == 'by_university':
        try:
            university_index = int(update.message.text[1:]) 
            university_name = list(set(program['name'] for program in PROGRAMS_DATA))[university_index]
            filtered_programs = [program for program in PROGRAMS_DATA if
                                 program['name'] == university_name and
                                 (
                                         (education_level == 'bachelor' and program.get('baccalaureate')) or
                                         (education_level == 'master' and program.get('magistracy')) or
                                         (education_level == 'doctorate' and program.get('doctorate'))
                                 )]
        except (ValueError, IndexError):
            filtered_programs = []

    elif search_method == 'by_specialty':
        search_query = update.message.text.lower()
        filtered_programs = [program for program in PROGRAMS_DATA if
                             search_query in program.get('baccalaureate_kz', '').lower() or
                             search_query in program.get('baccalaureate', '').lower() or
                             search_query in program.get('magistracy_kz', '').lower() or
                             search_query in program.get('magistracy', '').lower() or
                             search_query in program.get('doctorate_kz', '').lower() or
                             search_query in program.get('doctorate', '').lower()]
    else:
        filtered_programs = []

    if filtered_programs:
        text = "✅ *Результаты поиска:*\n\n"
        for program in filtered_programs:
            text += f"<b>{program['name']}</b>\n"  
            if education_level == 'bachelor':
                text += f"• *Программа:* {program.get('baccalaureate', '')}\n"
            elif education_level == 'master':
                text += f"• *Программа:* {program.get('magistracy', '')}\n"
            elif education_level == 'doctorate':
                text += f"• *Программа:* {program.get('doctorate', '')}\n"
            text += f"• *Код:* <code>{program.get('name', '')}</code>\n\n"
        await update.message.reply_text(text, parse_mode='HTML')
    else:
        text = "😔 *Программы не найдены.*"
        await update.message.reply_text(text, parse_mode='Markdown')
    return ConversationHandler.END

def main() -> None:
    """Запускает бота."""
    application = ApplicationBuilder().token(TOKEN).build()

    #/help
    application.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_EDUCATION_LEVEL: [MessageHandler(filters.COMMAND, choose_education_level)],
            CHOOSE_SEARCH_METHOD: [MessageHandler(filters.COMMAND, choose_search_method)],
            SHOW_PROGRAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_programs)],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()