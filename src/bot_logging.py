import logging

logger = logging.getLogger('discord')
log_level = logging.INFO
logger.setLevel(log_level)
log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
terminal_handler = logging.StreamHandler()
file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
terminal_handler.setLevel(log_level)
file_handler.setLevel(log_level)
terminal_handler.setFormatter(log_formatter)
file_handler.setFormatter(log_formatter)
logger.addHandler(terminal_handler)
logger.addHandler(file_handler)
