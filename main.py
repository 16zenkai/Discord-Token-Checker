import colorama
import time
import ctypes
import concurrent.futures
import msvcrt
import os
import json
import random
import threading
import pystyle
import toml
from curl_cffi import requests as request
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

Fore.GRAY = "\033[38;5;244m"
Fore.DARK_BLUE = "\033[38;5;19m"
Fore.VIOLET = "\033[38;5;129m"
Fore.PINK = "\033[38;5;205m"
Fore.ORANGE = "\033[38;5;208m"
Fore.LIGHT_BLUE = "\033[38;5;39m"

class Logger:
    def __init__(self):
        self.BLUE = "\033[38;5;27m"
        self.GRAY = "\033[38;5;244m"
        self.DARK_BLUE = "\033[38;5;19m"
        self.GREEN = "\033[38;5;46m"
        self.YELLOW = "\033[38;5;226m"
        self.CYAN = "\033[38;5;51m"
        self.WHITE = "\033[38;5;231m"
        self.RED = "\033[38;5;196m"
        self.PINK = "\033[38;5;205m"
        self.ORANGE = "\033[38;5;208m"
        self.LIGHT_BLUE = "\033[38;5;39m"
        self.VIOLET = "\033[38;5;129m"
        self.RESET = "\033[0m"
        self.prefix = f"{self.BLUE}{self.DARK_BLUE}{self.RESET}"
        self.last_print_time = 0
        self.print_lock = threading.Lock()

    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")

    def _log(self, color, icon, tag, message, **kwargs):
        with self.print_lock:
            time.sleep(0.01)  # Small delay to ensure proper line separation
            time_str = f"{self.GRAY}[{self.get_time()}]{self.RESET}"
            tag_str = f"{self.GRAY}[{color}{icon} {tag}{self.GRAY}]{self.RESET}"
            
            colored_kwargs = []
            for k, v in kwargs.items():
                if k == 'token':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.CYAN}{v}")
                elif k == 'type':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.GREEN}{v}")
                elif k == 'age':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.CYAN}{v}")
                elif k == 'boost':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.PINK}{v}")
                elif k == 'nitro':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.PINK}{v}")
                elif k == 'redeemable':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.LIGHT_BLUE}{v}")
                elif k == 'cooldown':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.VIOLET}{v}")
                elif k == 'error':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.RED}{v}")
                elif k == 'retry_after':
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.YELLOW}{v}")
                else:
                    colored_kwargs.append(f"{self.WHITE}{k}: {self.CYAN}{v}")
            
            extra_str = ' | '.join(colored_kwargs) if colored_kwargs else ''
            if extra_str:
                print(f"{self.prefix}{time_str} {tag_str} {color}→ {self.WHITE}{message}{self.RESET} | {extra_str}", flush=True)
            else:
                print(f"{self.prefix}{time_str} {tag_str} {color}→ {self.WHITE}{message}{self.RESET}", flush=True)

    def info(self, msg, **kwargs):
        self._log(self.CYAN, "ℹ", "INFO", msg, **kwargs)

    def success(self, msg, **kwargs):
        self._log(self.GREEN, "✓", "SUCCESS", msg, **kwargs)

    def fail(self, msg, **kwargs):
        self._log(self.RED, "✗", "FAIL", msg, **kwargs)

    def warning(self, msg, **kwargs):
        self._log(self.YELLOW, "⚠", "WARNING", msg, **kwargs)

log = Logger()

BANNER = r'''                                                                                                                          
'''

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    colors = [Fore.BLUE, Fore.LIGHTBLUE_EX, Fore.BLUE]
    lines = BANNER.split('\n')
    for i, line in enumerate(lines):
        if line.strip():  # Only print non-empty lines
            color = colors[i % len(colors)]
            print(pystyle.Center.XCenter(f"{color}{line}{Style.RESET_ALL}"))
    
    print(pystyle.Center.XCenter(f"{Fore.WHITE}Developer: {Fore.WHITE}zenkai. @netbanking {Fore.PINK}</> {Fore.WHITE} {Fore.WHITE}{Style.RESET_ALL}"))
    print()

with open('tokens.txt', 'r', encoding='utf-8') as f:
    tokens = f.readlines()
with open('data/proxies.txt', 'r', encoding='utf-8') as f:
    proxies = [line.strip() for line in f.readlines() if line.strip()]

tokens = list(set(tokens))

valid = 0
invalid = 0
locked = 0
nitro = 0
flagged = 0
total = len(tokens)
current = 0
no_nitro = 0
redeemable = 0
non_redeemable = 0
done = False

config = toml.load('data/config.toml')
settings = json.loads(open('data/settings.json', 'r', encoding='utf-8').read())

LOCK = threading.Lock()
TOKEN_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
MAX_RETRIES_PER_TOKEN = 3
REQUEST_TIMEOUT = 20

print_banner()

output_folder = f"output/{time.strftime('%Y-%m-%d %H-%M-%S')}"
log.info('Loading tokens...', output=output_folder, total=total)
print()

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

start = time.time()
rate_limit_cooldown = 0
rate_limit_lock = threading.Lock()


class Checker:
    def __init__(self) -> None:
        self.new_session()

    def new_session(self) -> None:
        self.session = request.Session(impersonate='chrome131')
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        if not config['main'].get('proxyless', True) and proxies:
            try:
                proxy = random.choice(proxies)
                self.session.proxies = {'http': proxy, 'https': proxy}
            except Exception:
                pass

    def retry_errors(self, e):
        err = str(e).lower()
        return (
            'connection' in err or 'timeout' in err or 'reset' in err or
            'refused' in err or 'network' in err or 'curl' in err or
            'ssl' in err or 'certificate' in err or 'remote host' in err or
            'closed' in err or 'abruptly' in err
        )

    def check(self) -> None:
        global flagged, no_nitro, nitro, non_redeemable
        global locked, redeemable, invalid, valid, current, rate_limit_cooldown

        TOKEN_LOCK.acquire()
        if not tokens:
            TOKEN_LOCK.release()
            return
        token = tokens.pop().strip()
        TOKEN_LOCK.release()

        token_only = token.split(':')[-1]
        half_token = token_only[:20]
        masked_token = half_token + '.***.*****'
        args = {'token': masked_token}

        for attempt in range(MAX_RETRIES_PER_TOKEN):
            try:
                with rate_limit_lock:
                    if rate_limit_cooldown > time.time():
                        wait = rate_limit_cooldown - time.time()
                        time.sleep(wait)

                self.session.headers['authorization'] = token_only

                r = self.session.get('https://discord.com/api/v9/users/@me/guilds', timeout=REQUEST_TIMEOUT)

                if r.status_code == 429:
                    retry_after = r.json().get('retry_after', 5)
                    log.warning('Rate limited', retry_after=f'{retry_after}s', token=masked_token)
                    with rate_limit_lock:
                        rate_limit_cooldown = time.time() + retry_after
                    time.sleep(retry_after)
                    TOKEN_LOCK.acquire()
                    tokens.append(token)
                    TOKEN_LOCK.release()
                    break

                current += 1

                if r.status_code == 401:
                    invalid += 1
                    log.fail('Invalid', token=masked_token)
                    LOCK.acquire()
                    with open(f'{output_folder}/invalid.txt', 'a', encoding='utf-8') as f:
                        f.write(token + '\n')
                    LOCK.release()
                    break

                if r.status_code == 403:
                    locked += 1
                    log.fail('Locked', token=masked_token)
                    LOCK.acquire()
                    with open(f'{output_folder}/locked.txt', 'a', encoding='utf-8') as f:
                        f.write(token + '\n')
                    LOCK.release()
                    break

                if r.status_code != 200:
                    raise Exception(f'Unexpected status {r.status_code}')

                r = self.session.get('https://discord.com/api/v9/users/@me', timeout=REQUEST_TIMEOUT)
                if r.status_code != 200:
                    raise Exception('users @me failed')

                try:
                    user_data = r.json()
                except Exception:
                    user_data = {}

                if not isinstance(user_data, dict):
                    user_data = {}

                if settings['flagged'] and (user_data.get('flags') or 0) & 1048576 == 1048576:
                    flagged += 1
                    log.fail('Flagged', **args)
                    LOCK.acquire()
                    with open(f'{output_folder}/flagged.txt', 'a', encoding='utf-8') as f:
                        f.write(token + '\n')
                    LOCK.release()
                    break

                if settings['type']:
                    type_name = 'Unclaimed'
                    if user_data.get('email') and user_data.get('verified'):
                        type_name = 'Email verified'
                    if user_data.get('phone'):
                        type_name = 'Fully verified' if type_name == 'Email verified' else 'Phone verified'
                else:
                    type_name = 'Valid'

                args['type'] = type_name

                if settings['age']:
                    try:
                        uid = int(user_data.get('id') or 0)
                        created_at = ((uid >> 22) + 1420070400000) / 1000
                        age_days = int((time.time() - created_at) / 86400)
                        age_str = f'{age_days} days'
                        args['age'] = age_str
                        age_path = f'{output_folder}/Age/{age_days} days'
                        if not os.path.exists(age_path):
                            os.makedirs(age_path)
                        LOCK.acquire()
                        with open(f'{age_path}/{type_name}.txt', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        LOCK.release()
                    except Exception:
                        pass

                if settings['nitro']:
                    try:
                        r2 = self.session.get('https://discord.com/api/v9/users/@me/billing/subscriptions', timeout=REQUEST_TIMEOUT)
                        data = r2.json() if r2.status_code == 200 else []

                        if isinstance(data, list) and data:
                            for sub in data:
                                if not isinstance(sub, dict):
                                    continue
                                end = sub.get('current_period_end')
                                if not end:
                                    continue

                                days_left = (
                                    time.mktime(time.strptime(end.replace('Z', '+00:00')[:26], '%Y-%m-%dT%H:%M:%S.%f'))
                                    - time.time()
                                ) / 86400

                                r3 = self.session.get('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', timeout=REQUEST_TIMEOUT)
                                slots = r3.json() if r3.status_code == 200 else []
                                available = sum(
                                    1 for s in (slots if isinstance(slots, list) else [])
                                    if isinstance(s, dict) and s.get('cooldown_ends_at') is None
                                )

                                month = '1 Month' if days_left <= 31 else '3 Month'
                                args['boost'] = available
                                args['nitro'] = f'{month} [{days_left:.0f}d]'
                                nitro += 1

                                cooldown = sub.get('cooldown_ends_at')
                                if cooldown is None:
                                    path = f'{output_folder}/Nitro/No Cooldown/{month}/{days_left:.0f} days'
                                    if not os.path.exists(path):
                                        os.makedirs(path)
                                    LOCK.acquire()
                                    with open(f'{path}/{available} boosts.txt', 'a', encoding='utf-8') as f:
                                        f.write(token + '\n')
                                    LOCK.release()
                                    args['cooldown'] = 'No Cooldown'
                                else:
                                    dt_obj = datetime.fromisoformat(str(cooldown).replace('Z', '+00:00'))
                                    cd = f'{dt_obj.day}d {dt_obj.hour}hrs'
                                    path = f'{output_folder}/Nitro/Cooldown/{month}/{days_left:.0f} days'
                                    if not os.path.exists(path):
                                        os.makedirs(path)
                                    LOCK.acquire()
                                    with open(f'{path}/{cd}.txt', 'a', encoding='utf-8') as f:
                                        f.write(token + '\n')
                                    LOCK.release()
                                    args['cooldown'] = cd
                        else:
                            LOCK.acquire()
                            args['boost'] = 0
                            args['nitro'] = 'No Nitro'
                            with open(f'{output_folder}/No Nitro.txt', 'a', encoding='utf-8') as f:
                                f.write(token + '\n')
                            LOCK.release()
                            no_nitro += 1
                    except Exception:
                        LOCK.acquire()
                        args['boost'] = 0
                        args['nitro'] = 'No Nitro'
                        with open(f'{output_folder}/No Nitro.txt', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        no_nitro += 1
                        LOCK.release()

                if settings['redeemable']:
                    try:
                        r2 = self.session.get('https://discord.com/api/v9/users/@me/billing/subscriptions?include_inactive=true', timeout=REQUEST_TIMEOUT)
                        if r2.status_code == 200 and isinstance(r2.text, str):
                            if '[]' in r2.text:
                                args['redeemable'] = 'Redeemable'
                                with open(f'{output_folder}/Redeemable.txt', 'a', encoding='utf-8') as f:
                                    f.write(token + '\n')
                                redeemable += 1
                            else:
                                args['redeemable'] = 'Non Redeemable'
                                with open(f'{output_folder}/Non Redeemable.txt', 'a', encoding='utf-8') as f:
                                    f.write(token + '\n')
                                non_redeemable += 1
                    except Exception:
                        pass

                valid += 1
                log.success('Valid', **args)
                LOCK.acquire()
                with open(f'{output_folder}/{type_name}.txt', 'a', encoding='utf-8') as f:
                    f.write(token + '\n')
                with open(f'{output_folder}/Valid.txt', 'a', encoding='utf-8') as f:
                    f.write(token + '\n')
                LOCK.release()
                break

            except Exception as e:
                if TOKEN_LOCK.locked():
                    try:
                        TOKEN_LOCK.release()
                    except Exception:
                        pass

                if not self.retry_errors(e) or attempt >= MAX_RETRIES_PER_TOKEN - 1:
                    TOKEN_LOCK.acquire()
                    tokens.append(token)
                    TOKEN_LOCK.release()
                    log.fail('Error', **args, error=str(e)[:50])

                self.new_session()
                time.sleep(0.5 + random.uniform(0, 0.5))


def update_title():
    while not done:
        try:
            time.sleep(0.5)  # Increased sleep time to reduce CPU usage
            if total > 0:  # Avoid division by zero
                elapsed = max(time.time() - start, 0.001)
                pct = current / total * 100
                cps = current / elapsed if elapsed else 0
                ctypes.windll.kernel32.SetConsoleTitleW(
                    f'Zenkai - Token Checker | Valid: {valid} | Invalid: {invalid} | '
                    f'Locked: {locked} | Remaining: {len(tokens)} | '
                    f'Checked: {pct:.2f}% | CPS: {cps:.2f}'
                )
        except Exception:
            pass


def wait_for_enter():
    print()  # Add newline before waiting
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':
                break
        time.sleep(0.1)  # Small sleep to reduce CPU usage
    log.info('Exiting in 3 seconds...')
    time.sleep(3)


if __name__ == '__main__':
    time.sleep(0.1)
    update = threading.Thread(target=update_title, daemon=True)
    update.start()
    
    threads = config['main']['threads']
    log.info(f'Starting with {threads} threads...')
    print()  # Add newline for better separation
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i in range(threads):
            checker = Checker()
            future = executor.submit(checker.check)
            futures.append(future)
        
        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            pass
    
    done = True
    update.join(timeout=1)
    print()  # Add newline before final summary
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    log.info(f'Checked {current} tokens in {minutes} minutes and {seconds} seconds')
    
    print(f"\n{Fore.BLUE}{'═' * 70}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}╭─{Fore.WHITE} FINAL SUMMARY {Fore.BLUE}────────────────────────────────────────────────────────────────╮")
    print(f"│ {Fore.WHITE}Checked: {Fore.CYAN}{current:<6} {Fore.WHITE}| Valid: {Fore.GREEN}{valid:<6} {Fore.WHITE}| Invalid: {Fore.ORANGE}{invalid:<6} {Fore.WHITE}| Nitro: {Fore.PINK}{nitro:<6} {Fore.WHITE}             |")
    print(f"│ {Fore.WHITE}Locked: {Fore.RED}{locked:<6} {Fore.WHITE}| Flagged: {Fore.YELLOW}{flagged:<6} {Fore.WHITE}| Redeemable: {Fore.LIGHT_BLUE}{redeemable:<6} {Fore.WHITE}| Non Redeemable: {Fore.VIOLET}{non_redeemable:<6} {Fore.WHITE}|")
    print(f"{Fore.BLUE}╰────────────────────────────────────────────────────────────────────────────────╯{Style.RESET_ALL}")
    print(f"{Fore.PINK} bas cutie ab band karo aur sojao <3 {Style.RESET_ALL}")
    print()  # Add newline before exit prompt
    
    log.info('Press Enter to exit.')
    wait_for_enter()