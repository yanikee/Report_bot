import logging

from bot import ReportBot
from const import TOKEN


bot = ReportBot()

bot.run(TOKEN, log_level=logging.WARNING)
