import colorama
from colorama import Fore, Style
from datetime import datetime

colorama.init(autoreset=True)

Fore.GRAY = "\033[38;5;244m"
Fore.DARK_BLUE = "\033[38;5;19m"
Fore.VIOLET = "\033[38;5;129m"

def _format(tag, color, msg, **kwargs):
    time_str = datetime.now().strftime('%H:%M:%S')
    extras = ' | '.join(f'{k}: {v}' for k, v in kwargs.items())
    extra_str = f' | {extras}' if extras else ''
    print(f"{Fore.BLUE} {Fore.DARK_BLUE} {Fore.GRAY}[{time_str}] {color}[{tag}]{Style.RESET_ALL} → {msg}{extra_str}")

def info(msg, **kwargs):
    _format('INFO', Fore.CYAN, msg, **kwargs)

def success(msg, **kwargs):
    _format('SUCCESS', Fore.GREEN, msg, **kwargs)

def error(msg, **kwargs):
    _format('ERROR', Fore.RED, msg, **kwargs)

def warning(msg, **kwargs):
    _format('WARNING', Fore.YELLOW, msg, **kwargs)

def token(msg, **kwargs):
    _format('TOKEN', Fore.MAGENTA, msg, **kwargs)