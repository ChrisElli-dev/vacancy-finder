import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from finder_headhunter import finder_headhunter

parser = finder_headhunter()

CITY_IDS = {
    'Moscow': 1,
    'Saint Petersburg': 2,
}

CHOOSING, SETTING_MIN_SALARY, SETTING_LOCATION, SETTING_VACANCY_COUNT = range(4)

def get_user_settings(context):
    if 'settings' not in context.chat_data:
        context.chat_data['settings'] = {
            'vacancy_count': 5,
            'salary_min': None,
            'location': None,
        }
    return context.chat_data['settings']

def main():
    updater = Updater(os.getenv('TELEGRAM_TOKEN'), use_context=True)
    dp = updater.dispatcher

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler('settings', settings)],
        states={
            CHOOSING: [
                CallbackQueryHandler(set_vacancy_count, pattern='set_vacancy_count'),
                CallbackQueryHandler(set_min_salary, pattern='set_min_salary'),
                CallbackQueryHandler(set_location, pattern='set_location')
            ],
            SETTING_VACANCY_COUNT: [MessageHandler(Filters.text & ~Filters.command, handle_vacancy_count)],
            SETTING_MIN_SALARY: [MessageHandler(Filters.text & ~Filters.command, handle_min_salary)],
            SETTING_LOCATION: [MessageHandler(Filters.text & ~Filters.command, handle_location)]
        },
        fallbacks=[CommandHandler('settings', settings)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(settings_handler)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Enter the job title or use /settings to configure search parameters.'
    )

def settings(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Number of vacancies", callback_data='set_vacancy_count')],
        [InlineKeyboardButton("Set minimum salary", callback_data='set_min_salary')],
        [InlineKeyboardButton("Search location", callback_data='set_location')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a parameter to configure:', reply_markup=reply_markup)
    return CHOOSING

def set_vacancy_count(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('Enter the number of vacancies you want to see at a time:')
    return SETTING_VACANCY_COUNT

def set_min_salary(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('Enter the minimum salary:')
    return SETTING_MIN_SALARY

def set_location(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('Enter the location for the search:')
    return SETTING_LOCATION

def handle_vacancy_count(update: Update, context: CallbackContext):
    try:
        count = int(update.message.text)
        user_settings = get_user_settings(context)
        user_settings['vacancy_count'] = count
        update.message.reply_text(f'The number of vacancies is set to {count}.')
    except ValueError:
        update.message.reply_text('Please enter a numeric value.')
    return ConversationHandler.END

def handle_min_salary(update: Update, context: CallbackContext):
    try:
        salary = int(update.message.text)
        user_settings = get_user_settings(context)
        user_settings['salary_min'] = salary
        update.message.reply_text(f'Minimum salary is set to {salary}.')
    except ValueError:
        update.message.reply_text('Please enter a numeric value.')
    return ConversationHandler.END

def handle_location(update: Update, context: CallbackContext):
    location = update.message.text
    user_settings = get_user_settings(context)
    user_settings['location'] = CITY_IDS.get(location, None)
    if user_settings['location'] is None:
        update.message.reply_text(f'Unknown location: {location}. Please enter a valid city name.')
    else:
        update.message.reply_text(f'Search location is set to {location}.')
    return ConversationHandler.END

def handle_message(update: Update, context: CallbackContext):
    query = update.message.text
    update.message.reply_text('Searching for vacancies...')

    user_settings = get_user_settings(context)
    vacancies = parser.get_vacancies(query, salary=user_settings['salary_min'], location=user_settings['location'])
    parser.save_to_db(vacancies)

    responses = []
    count = 0
    for item in vacancies.get('items', []):
        if user_settings['location'] and str(user_settings['location']) not in item.get('area', {}).get('id', ''):
            continue
        if count >= user_settings['vacancy_count']:
            break
        title = item['name']
        skills = ', '.join(skill['name'] for skill in item.get('key_skills', [])) if item.get('key_skills') else 'Not specified'
        employment_type = item.get('employment', {}).get('name', 'Not specified')
        salary = f"{item['salary']['from']} {item['salary']['currency']}" if item.get('salary') else 'Not specified'
        location = item.get('area', {}).get('name', 'Not specified')
        experience = item.get('experience', {}).get('name', 'Not specified')
        url = item.get('alternate_url', 'No link')

        response = (f"Title: {title}\n"
                    f"Skills: {skills}\n"
                    f"Employment type: {employment_type}\n"
                    f"Salary: {salary}\n"
                    f"Location: {location}\n"
                    f"Experience level: {experience}\n"
                    f"Vacancy link: {url}\n")
        responses.append(response)
        count += 1

    for response in responses:
        update.message.reply_text(response)

if __name__ == '__main__':
    main()
