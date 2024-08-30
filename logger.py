import logging
from colorama import init, Fore, Style

# Initialize Colorama
init(autoreset=True)

class ColoramaFormatter(logging.Formatter):
    """ Custom formatter to add Colorama colors to log output """
    level_to_color = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        color = self.level_to_color.get(record.levelno, Fore.WHITE)  # Default to white if level not set
        message = super().format(record)
        return color + message

def setup_logger(name='my_logger'):
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Or any other level

    # Check if handlers have been added already
    if not logger.handlers:
        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create formatter and add it to the handler
        formatter = ColoramaFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
