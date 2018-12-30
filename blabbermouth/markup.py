from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup


def InlineButton(text, callback_data):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback_data)]
        ]
    )
