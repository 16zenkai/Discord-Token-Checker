# Discord Token Checker

A multi-threaded Discord token checker with proxy support, Nitro detection, redeemable checks, token categorization, and detailed logging.

## Features

- Valid / Invalid / Locked token checking
- Nitro detection
- Redeemable Nitro checking
- Flagged token detection
- Account age sorting
- Token type detection
- Proxy support
- Multi-threaded checker
- Automatic retries
- Real-time console stats
- Organized output folders
- Custom logging system

---

# Setup

## Install Python

Download Python 3.11+:

https://www.python.org/downloads/

Enable:

- Add Python to PATH

---

# Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install colorama pystyle toml curl_cffi
```

---

# Folder Structure

```text id="2rv3pb"
data/
├── config.toml
├── settings.json
└── proxies.txt

output/
└── generated automatically

tokens.txt
main.py
```

---

# tokens.txt

Put 1 token per line.

Example:

```text id="owxk1f"
token_here
token_here
```

Combo formats also supported:

```text id="5ykxll"
email:password:token
user:pass:token
```

---

# proxies.txt

Supported formats:

```text id="7tb7q1"
ip:port
http://ip:port
http://user:pass@ip:port
```

Leave empty for proxyless mode.

---

# config.toml

Example:

```toml id="rwx0qf"
[main]
threads = 50
proxyless = true
```

---

# settings.json

Example:

```json id="z1fxl6"
{
  "flagged": true,
  "type": true,
  "age": true,
  "nitro": true,
  "redeemable": true
}
```

---

# Running

```bash id="8xgq4o"
python main.py
```

---

# Output

Results are automatically sorted into folders.

Example:

```text id="0t2v26"
output/
├── Valid.txt
├── Invalid.txt
├── Locked.txt
├── Flagged.txt
├── Redeemable.txt
├── Non Redeemable.txt
├── Nitro/
└── Age/
```

---

# Features Explained

## Token Types

- Unclaimed
- Email Verified
- Phone Verified
- Fully Verified

---

## Nitro Detection

Checks:

- Nitro status
- Remaining days
- Available boosts
- Cooldowns
- Redeemability

---

## Age Sorting

Tokens are sorted by account age automatically.

Example:

```text id="stpk2v"
Age/
├── 30 days/
├── 100 days/
└── 300 days/
```

---

# Notes

- Good proxies improve performance
- Duplicate tokens are removed automatically
- Tokens retry automatically on network errors
- Rate limits are handled automatically
- Output folders are timestamped

---

# Requirements

- Python 3.11+
- Windows recommended

---

# Credits

Developer: zenkai
