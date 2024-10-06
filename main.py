import requests
import time
import json
from colorama import init, Fore, Style
from itertools import cycle
from pyfiglet import Figlet
import os

init(autoreset=True) 

def read_encrypted_config():
    try:
        with open('core/config.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(Fore.RED + "File konfigurasi tidak ditemukan.")
        return None
    except json.JSONDecodeError:
        print(Fore.RED + "File konfigurasi tidak valid.")
        return None

ENCRYPTED_CONFIG = read_encrypted_config()

if ENCRYPTED_CONFIG is None:
    print(Fore.RED + "Gagal membaca konfigurasi. Program berhenti.")
    exit(1)

def decrypt_config(encrypted_data, key):
    decrypted = ''
    for i, char_code in enumerate(encrypted_data):
        decrypted += chr(char_code ^ ord(key[i % len(key)]))
    return json.loads(decrypted)

_a, _b, _c = 'Kal', 'ong', 'Crypto'
_key = _a + _b + _c

config = decrypt_config(ENCRYPTED_CONFIG, _key)

class PipWorld:
    def __init__(self, authorization, user_agent, do_quests, account_number):
        self.session = requests.Session()
        self.base_url = config['base_url']
        self.api_url = config['api_url']
        self.dynamic_variables = {}
        self.authorization = authorization
        self.user_agent = user_agent
        self.do_quests = do_quests
        self.account_number = account_number

    def tap(self):
        print(Fore.CYAN + Style.BRIGHT + config['messages']['start_bot'])
        print(Fore.YELLOW + config['messages']['starting_bot'])
        print(Fore.CYAN + f"Mengerjakan akun #{self.account_number}")
        
        response = self.session.post(f'{self.api_url}/app/post/tapHandler', 
            headers={
                'content-type': 'application/json',
                'authorization': self.authorization,
                'user-agent': self.user_agent,
            }, 
            json={"coins": config['tap_coins']}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                user = data['user']
                
                print(Fore.GREEN + "\n Login")
                print(Fore.WHITE + "Account")
                print(Fore.CYAN + f" Pengguna: {user['firstName']} {user['lastName']}")
                print(Fore.MAGENTA + f" Level: {user['level']['level']} ({user['level']['title']})")
                print(Fore.YELLOW + f" Saldo baru: {user['balance']} Point")
                print(Fore.BLUE + f" Energi: {user['energy']}/{user['maxUserEnergy']}")
                print(Fore.RED + f" Streak: {user['streak']['count']} hari")
                print(Fore.GREEN + f" Point per tap: {user['coinsPerTap']}")
                
                if user['passiveIncomePerHour'] > 0:
                    print(Fore.YELLOW + f" Pendapatan pasif: {user['passiveIncomePerHour']} Point/jam")
                
                print(Fore.WHITE + "Berhasil")
                print(Fore.YELLOW + config['messages']['quest_skipped'])
                
            except json.JSONDecodeError:
                print(Fore.RED + config['error_messages']['invalid_json'])
            except KeyError as e:
                print(Fore.RED + config['error_messages']['incomplete_data'].format(str(e)))
        else:
            print(Fore.RED + config['error_messages']['request_failed'].format(response.status_code))

    def quests(self):
        if not self.do_quests:
            print(Fore.YELLOW + config['messages']['quest_skipped'])
            return

        print(Fore.CYAN + Style.BRIGHT + config['messages']['quest_header'])
        headers = {
            'authorization': self.authorization,
            'Content-Type': 'application/json',
            'user-agent': self.user_agent
        }
        response = self.session.get(f'{self.api_url}/app/get/getQuests', headers=headers)
        
        if response.status_code != 200:
            print(Fore.RED + config['error_messages']['quest_list_failed'].format(response.status_code))
            return

        quests_data = response.json()
        quests = quests_data if isinstance(quests_data, list) else quests_data.get('quests', [])

        for quest in quests:
            quest_id = quest.get('id')
            quest_description = quest.get('description', '').split('.')[0] 
            quest_data = {"questId": quest_id}
            response = self.session.post(f'{self.api_url}/app/post/checkQuest', 
                headers=headers, 
                json=quest_data
            )
            
            if response.status_code == 200:
                print(Fore.GREEN + f"? Quest berhasil dikerjakan: {quest_description}")
            else:
                try:
                    error_message = response.json().get('message', '')
                    if "expired" not in error_message.lower():
                        if "already completed" in error_message.lower():
                            print(Fore.BLUE + f"?? {quest_description} - {error_message}")
                        else:
                            print(Fore.YELLOW + f"?? {quest_description} - {error_message}")
                except json.JSONDecodeError:
                    print(Fore.RED + config['error_messages']['quest_execution_failed'].format(quest_description))
            
            time.sleep(0)

        print(Fore.CYAN + "Quest selesai.")

def text(text):
    f = Figlet(font='slant')
    ascii_art = f.renderText(text)
    lines = ascii_art.split('\n')
    for line in lines:
        print(Fore.CYAN + line)
        time.sleep(0.1)
    time.sleep(1)
    os.system('cls' if os.name == 'nt' else 'clear')

def read_authorizations():
    try:
        with open(config['file_names']['auth_file'], 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + config['error_messages']['auth_file_not_found'])
        return []
    except IOError:
        print(Fore.RED + config['error_messages']['auth_file_error'])
        return []

def read_user_agents():
    try:
        with open(config['file_names']['user_agent_file'], 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + config['error_messages']['user_agent_file_not_found'])
        return [config['default_user_agent']]
    except IOError:
        print(Fore.RED + config['error_messages']['user_agent_file_error'])
        return [config['default_user_agent']]

def get_user_choice():
    print(Fore.CYAN + config['messages']['join_channel'] + Fore.GREEN + f"[{config['channel_info']['name']}]({config['channel_info']['url']})")
    print(Fore.CYAN + config['messages']['get_updates'])
    print()
    
    while True:
        choice = input(Fore.CYAN + config['messages']['quest_choice']).lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        print(Fore.RED + config['messages']['invalid_choice'])

def run():
    text(config['channel_info']['name'])
    
    authorizations = read_authorizations()
    user_agents = read_user_agents()
    if not authorizations:
        print(Fore.RED + config['error_messages']['no_valid_auth'])
        return

    user_agent_cycle = cycle(user_agents)
    do_quests = get_user_choice()

    print(Fore.CYAN + Style.BRIGHT + "=== Pip World Bot ===")
    print(Fore.YELLOW + "Memulai Bot")
    print(Fore.MAGENTA + f"Jumlah akun: {len(authorizations)}")

    while True:
        for index, auth in enumerate(authorizations, start=1):
            user_agent = next(user_agent_cycle)
            Eksekusi = PipWorld(auth, user_agent, do_quests, index)
            try:
                Eksekusi.tap()
                if do_quests:
                    Eksekusi.quests()
            except requests.exceptions.RequestException as e:
                print(Fore.RED + config['error_messages']['simulation_error'].format(e))
            except Exception as e:
                print(Fore.RED + config['error_messages']['unexpected_error'].format(e))
            
            print(Fore.CYAN + config['messages']['wait_next_account'])
            time.sleep(1)
        
        print(Fore.MAGENTA + config['messages']['all_accounts_processed'].format(config['wait_time']))
        for i in range(config['wait_time'], 0, -1):
            print(f"\rMemulai dalam {i} detik...", end="", flush=True)
            time.sleep(1)
        print("\n")

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print(Fore.RED + config['messages']['bot_stopped'])