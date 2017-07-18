from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..models import User
from ..definitions import commands_set, pending_user_actions


class KeyboardBuild:
    @staticmethod
    def inline(buttons: list, cancel_button_name=None):
        inline_keyboard = \
            [[InlineKeyboardButton(button[0], callback_data=button[1]) for button in row] for row in buttons if row]
        if cancel_button_name:
            inline_keyboard.append([InlineKeyboardButton(cancel_button_name, 'c_cancel')])
        return InlineKeyboardMarkup(inline_keyboard)

    @staticmethod
    def default(user: User):
        buttons = [['Do not disturb' if user.is_active else 'Ready', 'Status'], ['Activities list', 'Report bug']]
        if user.pending_action != pending_user_actions['none']:
            buttons[0].insert(0, 'Cancel action')
        if user.has_right_to('p_summon'):
            buttons[1].insert(1, 'Summon friends')
        if user.has_right_to('su_full_information'):
            buttons[1].append('Full information')
        return ReplyKeyboardMarkup([[KeyboardButton(x) for x in row] for row in buttons], resize_keyboard=True)

    @staticmethod
    def summon_response(activity_name: str, is_selected_accept=None):
        buttons = [[]]
        if not is_selected_accept:
            buttons[0] += [('Join now', 'p_accept ' + activity_name), ('Coming', 'p_accept_later ' + activity_name)]
        if is_selected_accept or is_selected_accept is None:
            buttons[0].append(('Decline', 'p_decline ' + activity_name))
        return KeyboardBuild.inline(buttons)


class CallbackUtil:
    @staticmethod
    def edit(update: Update, text, reply_markup=None):
        if not update.callback_query:
            return
        if text:
            update.callback_query.edit_message_text(text=text, parse_mode='Markdown')
        if reply_markup:
            update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    @staticmethod
    def get_data(callback_data: str)->str:
        return callback_data.split(' ', 1)[1]

    @staticmethod
    def remove_message(bot: Bot, update: Update):
        if not bot.delete_message(chat_id=update.callback_query.message.chat_id,
                                  message_id=update.callback_query.message.message_id):
            CallbackUtil.edit(update, 'Message is not valid any more')


def callback_only(decorated_handler):
    def handler_wrapper(bot: Bot, update: Update):
        if update.callback_query:
            return decorated_handler(bot, update)
    return handler_wrapper


def _send_response(user: User, bot: Bot, response):
    if not response:
        return
    if isinstance(response, tuple):
        user.send_message(bot, text=response[0], reply_markup=response[1])
    else:
        user.send_message(bot, text=response)


def personal_command(command=None):
    if command:
        assert command in commands_set

    def personal_command_impl(decorated_handler):
        def decorated_handler_wrapper(bot: Bot, update: Update, user=None):
            if update.callback_query:
                update.callback_query.answer()

            if not user:
                user, is_created = User.get_or_create(telegram_user_id=update.effective_user.id,
                                                      defaults={'telegram_login': update.effective_user.name})
                if user.is_disabled_chat or user.telegram_login != update.effective_user.name:
                    user.telegram_login = update.effective_user.name
                    user.is_disabled_chat = False
                    user.save()
                if is_created:
                    User.send_message_to_superuser(bot, text='{0} joined'.format(user.telegram_login))

            if command and not user.has_right_to(command):
                _send_response(user, bot, ('Not enough rights', KeyboardBuild.default(user)))
            else:
                _send_response(user, bot, decorated_handler(bot, update, user))
        return decorated_handler_wrapper
    return personal_command_impl
