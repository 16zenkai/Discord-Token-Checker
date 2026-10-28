import colorama
import sys
import time
import ctypes
import concurrent.futures
import msvcrt
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import random
import threading
import pystyle
try:
    import toml
    def load_config(path):
        return toml.load(path)
except ImportError:
    import tomllib
    def load_config(path):
        with open(path, 'rb') as f:
            return tomllib.load(f)
from curl_cffi import requests as request
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# Extended custom colors using 256-color palette
Fore.GRAY = "\033[38;5;244m"
Fore.PURPLE = "\033[38;5;99m"      # Main thematic accent
Fore.NEON_PINK = "\033[38;5;201m"  # High priority highlights
Fore.CYAN_BLUE = "\033[38;5;38m"   # For info tags
Fore.MINT_GREEN = "\033[38;5;48m"  # For success tags
Fore.CORAL_RED = "\033[38;5;204m"  # For failures
Fore.GOLD = "\033[38;5;214m"       # For warnings

class Logger:
    def __init__(self):
        # Clean minimal palette
        self.DIM = "\033[38;5;240m"        # Subtle bracket/separator gray
        self.TIME_GRAY = "\033[38;5;244m"   # Timestamp gray
        self.KEY_GRAY = "\033[38;5;242m"    # Key labels (token:, status:, lock:)
        self.WHITE = "\033[38;5;253m"       # Main values
        self.SUCCESS = "\033[38;5;120m"    # Soft mint green (+)
        self.FAIL = "\033[38;5;203m"       # Soft coral red (-)
        self.WARN = "\033[38;5;214m"       # Warm orange (*)
        self.INFO = "\033[38;5;75m"        # Soft blue (/)
        self.PURPLE = "\033[38;5;141m"     # Soft purple (?)
        self.PINK = "\033[38;5;213m"       # Soft neon pink
        self.RESET = "\033[0m"
        self.print_lock = threading.Lock()

    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")

    def prefix(self, char, color):
        return f"{self.DIM}({color}{char}{self.DIM}){self.RESET}"

    def _log_token_status(self, char, char_color, tag, tag_color, status_text=None, **kwargs):
        with self.print_lock:
            time_str = f"{self.DIM}[{self.TIME_GRAY}{self.get_time()}{self.DIM}]{self.RESET}"
            pfx = self.prefix(char, char_color)
            tag_str = f"{tag_color}{tag:<6}{self.RESET}"
            sep = f"{self.DIM}»{self.RESET}"

            parts = []
            if 'token' in kwargs:
                parts.append(f"{self.KEY_GRAY}token:{self.RESET} {self.WHITE}{kwargs['token']}")
            if status_text:
                status_color = self.SUCCESS if status_text.lower() == 'valid' else (self.FAIL if status_text.lower() in ['locked', 'invalid'] else self.WHITE)
                parts.append(f"{self.KEY_GRAY}status:{self.RESET} {status_color}{status_text}")

            for k, v in kwargs.items():
                if k == 'token':
                    continue
                if k == 'lock':
                    parts.append(f"{self.KEY_GRAY}lock:{self.RESET} {self.WARN}{v}")
                elif k == 'type':
                    parts.append(f"{self.KEY_GRAY}type:{self.RESET} {self.SUCCESS}{v}")
                elif k in ['nitro', 'boost']:
                    parts.append(f"{self.KEY_GRAY}{k}:{self.RESET} {self.PINK}{v}")
                elif k == 'age':
                    parts.append(f"{self.KEY_GRAY}age:{self.RESET} {self.INFO}{v}")
                elif k == 'redeemable':
                    parts.append(f"{self.KEY_GRAY}redeemable:{self.RESET} {self.INFO}{v}")
                elif k in ['retry_after', 'cooldown']:
                    parts.append(f"{self.KEY_GRAY}{k}:{self.RESET} {self.WARN}{v}")
                elif k == 'error':
                    parts.append(f"{self.KEY_GRAY}error:{self.RESET} {self.FAIL}{v}")
                else:
                    parts.append(f"{self.KEY_GRAY}{k}:{self.RESET} {self.WHITE}{v}")

            details = f" {self.RESET}".join(parts)
            print(f"{time_str} {pfx} {tag_str} {sep} {details}{self.RESET}", flush=True)

    def success(self, msg='Valid', **kwargs):
        self._log_token_status('+', self.SUCCESS, 'VALID', self.SUCCESS, status_text=msg, **kwargs)

    def fail(self, msg, **kwargs):
        tag = msg.upper()
        if 'LOCK' in tag:
            tag = 'LOCKED'
        elif 'INVALID' in tag:
            tag = 'INVALID'
        elif 'FLAG' in tag:
            tag = 'FLAGGED'
        elif 'ERROR' in tag:
            tag = 'ERROR'
        self._log_token_status('-', self.FAIL, tag, self.FAIL, status_text=msg, **kwargs)

    def warning(self, msg, **kwargs):
        tag = 'RATELIMIT' if 'rate' in msg.lower() else 'WARN'
        self._log_token_status('*', self.WARN, tag, self.WARN, **kwargs)

    def log_line(self, char, char_color, text):
        with self.print_lock:
            time_str = f"{self.DIM}[{self.TIME_GRAY}{self.get_time()}{self.DIM}]{self.RESET}"
            pfx = self.prefix(char, char_color)
            print(f"{time_str} {pfx} {text}{self.RESET}", flush=True)

    def inf(self, text):
        self.log_line('/', self.INFO, text)

    def info(self, text, **kwargs):
        if kwargs:
            extra = ', '.join(f"{k}= {v}" for k, v in kwargs.items())
            self.inf(f"{text} -> {extra}")
        else:
            self.inf(text)

    def input(self, text):
        time_str = f"{self.DIM}[{self.TIME_GRAY}{self.get_time()}{self.DIM}]{self.RESET}"
        pfx = self.prefix('?', self.PURPLE)
        print(f"\n{time_str} {pfx} {self.INFO}{text}{self.RESET} ", end='', flush=True)

log = Logger()

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    purple = "\033[38;5;141m"
    dim = "\033[38;5;240m"
    gray = "\033[38;5;245m"
    white = "\033[38;5;255m"
    reset = "\033[0m"
    print(f"  {purple}Dev: {white}@16zenkai {dim}• {gray}{reset}")
    print()

with open('tokens.txt', 'r', encoding='utf-8') as f:
    tokens = f.readlines()
with open('data/proxies.txt', 'r', encoding='utf-8') as f:
    proxies = [line.strip() for line in f.readlines() if line.strip()]

tokens = list(set(tokens))

valid = 0
invalid = 0
locked = 0
email_locked = 0
phone_locked = 0
nitro = 0
flagged = 0
total = len(tokens)
current = 0
no_nitro = 0
redeemable = 0
non_redeemable = 0
done = False

config = load_config('data/config.toml')
settings = json.loads(open('data/settings.json', 'r', encoding='utf-8').read())

LOCK = threading.Lock()
TOKEN_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()
MAX_RETRIES_PER_TOKEN = 3
REQUEST_TIMEOUT = 20

print_banner()

output_folder = f"output/{time.strftime('%Y-%m-%d %H-%M-%S')}"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

threads = config['main']['threads']
log.inf(f"Total tokens loaded -> count= {total}")
log.inf(f"Output directory -> {output_folder}")
log.inf(f"Starting with {threads} threads")
print()

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
        global locked, email_locked, phone_locked, redeemable, invalid, valid, current, rate_limit_cooldown

        while True:
            TOKEN_LOCK.acquire()
            if not tokens:
                TOKEN_LOCK.release()
                break
            token = tokens.pop().strip()
            TOKEN_LOCK.release()

            token_only = token.split(':')[-1]
            masked_token = (token_only[:12] + '****') if len(token_only) >= 12 else token_only
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
                        lock_type = 'phone'
                        try:
                            r_user = self.session.get('https://discord.com/api/v9/users/@me', timeout=REQUEST_TIMEOUT)
                            if r_user.status_code == 200:
                                user_data = r_user.json()
                                if isinstance(user_data, dict):
                                    if not user_data.get('verified') or not user_data.get('email'):
                                        lock_type = 'email'
                                    else:
                                        lock_type = 'phone'
                            elif 'email' in r_user.text.lower():
                                lock_type = 'email'
                        except Exception:
                            pass

                        LOCK.acquire()
                        locked += 1
                        if lock_type == 'email':
                            email_locked += 1
                        else:
                            phone_locked += 1

                        with open(f'{output_folder}/locked.txt', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        lock_file_name = 'Email Locked.txt' if lock_type == 'email' else 'Phone Locked.txt'
                        with open(f'{output_folder}/{lock_file_name}', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        LOCK.release()

                        log.fail('Locked', token=masked_token, lock=lock_type)
                        break

                    if r.status_code != 200:
                        raise Exception(f'Unexpected status {r.status_code}')

                    r = self.session.get('https://discord.com/api/v9/users/@me', timeout=REQUEST_TIMEOUT)
                    if r.status_code == 403:
                        lock_type = 'phone'
                        try:
                            if 'email' in r.text.lower():
                                lock_type = 'email'
                        except Exception:
                            pass

                        LOCK.acquire()
                        locked += 1
                        if lock_type == 'email':
                            email_locked += 1
                        else:
                            phone_locked += 1

                        with open(f'{output_folder}/locked.txt', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        lock_file_name = 'Email Locked.txt' if lock_type == 'email' else 'Phone Locked.txt'
                        with open(f'{output_folder}/{lock_file_name}', 'a', encoding='utf-8') as f:
                            f.write(token + '\n')
                        LOCK.release()

                        log.fail('Locked', token=masked_token, lock=lock_type)
                        break

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
            time.sleep(0.5)  
            if total > 0:  
                elapsed = max(time.time() - start, 0.001)
                pct = current / total * 100
                cps = current / elapsed if elapsed else 0
                ctypes.windll.kernel32.SetConsoleTitleW(
                    f'Zenkai | Valid: {valid} | Invalid: {invalid} | '
                    f'Locked: {locked} (E: {email_locked} / P: {phone_locked}) | '
                    f'Checked: {pct:.1f}% | CPS: {cps:.1f}'
                )
        except Exception:
            pass


def wait_for_enter():
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':
                break
        time.sleep(0.05)
    print()


if __name__ == '__main__':
    time.sleep(0.1)
    update = threading.Thread(target=update_title, daemon=True)
    update.start()
    
    threads = config['main']['threads']
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i in range(threads):
            checker = Checker()
            future = executor.submit(checker.check)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            pass
    
    done = True
    update.join(timeout=1)
    
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    dim = "\033[38;5;240m"
    gray = "\033[38;5;245m"
    white = "\033[38;5;255m"
    green = "\033[38;5;120m"
    red = "\033[38;5;203m"
    gold = "\033[38;5;221m"
    pink = "\033[38;5;213m"
    cyan = "\033[38;5;75m"
    reset = "\033[0m"
    
    print()
    log.log_line('/', log.INFO, f"{white}Minutes {dim}-> {gray}count= {reset}{cyan}{minutes}{reset}{gray}, {white}Seconds {dim}-> {gray}count= {reset}{cyan}{seconds}{reset}")
    log.log_line('/', log.INFO, f"{white}Total {dim}-> {gray}count= {reset}{cyan}{total}{reset}")
    log.log_line('+', log.SUCCESS, f"{white}Valid {dim}-> {gray}count= {reset}{green}{valid}{reset}")
    log.log_line('-', log.FAIL, f"{white}Invalid {dim}-> {gray}count= {reset}{red}{invalid}{reset}")
    log.log_line('*', log.WARN, f"{white}Nitro {dim}-> {gray}count= {reset}{pink}{nitro}{reset}")
    log.log_line('-', log.FAIL, f"{white}Locked {dim}-> {gray}count= {reset}{red}{locked}{reset}")
    time_str = f"{dim}[{gray}{log.get_time()}{dim}]{reset}"
    print(f"{time_str}      {dim}├─ {white}Email Locked {dim}-> {gray}count= {reset}{gold}{email_locked}{reset}")
    print(f"{time_str}      {dim}└─ {white}Phone Locked {dim}-> {gray}count= {reset}{red}{phone_locked}{reset}")
    if flagged > 0:
        log.log_line('*', log.WARN, f"{white}Flagged {dim}-> {gray}count= {reset}{gold}{flagged}{reset}")
    if settings.get('redeemable'):
        log.log_line('/', log.INFO, f"{white}Redeemable {dim}-> {gray}count= {reset}{cyan}{redeemable}{reset}")
        log.log_line('/', log.INFO, f"{white}Non Redeemable {dim}-> {gray}count= {reset}{gray}{non_redeemable}{reset}")
    
    log.input("Press Enter to exit")
    wait_for_enter()
