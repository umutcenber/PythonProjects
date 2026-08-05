import requests
import time
from datetime import datetime

print('=' * 50)
print('        WEBSITE UPTIME MONITOR')
print('=' * 50)

websites = []

while True:
    url = input('Enter website URL (or type done): ').strip()

    if url.lower() == 'done':
        break

    if not url.startswith('http'):
        url = 'https://' + url

    websites.append(url)

if not websites:
    print('No websites entered.')
    exit()

log_file = 'log.txt'

print('\nChecking websites...\n')

with open(log_file, 'a', encoding='utf-8') as log:

    log.write(f'\n===== {datetime.now()} =====\n')

    for url in websites:

        try:
            start = time.time()

            response = requests.get(url, timeout=5)

            elapsed = (time.time() - start) * 1000

            status = response.status_code

            if status == 200:
                result = f'🟢 {url} | Status: {status} | {elapsed:.0f} ms'
            else:
                result = f'🟠 {url} | Status: {status} | {elapsed:.0f} ms'

        except requests.exceptions.RequestException as e:
            result = f'🔴 {url} | ERROR: {e}'

        print(result)
        log.write(result + '\n')

print(f'\n✅ Results saved to {log_file}')