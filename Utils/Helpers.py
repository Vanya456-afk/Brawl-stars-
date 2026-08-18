import json
import string
import random
from colorama import Fore


class Helpers:
    connected_clients = {"ClientsCount": 0, "Clients": {}}

    yellow = Fore.YELLOW
    green = Fore.GREEN
    blue = Fore.LIGHTBLUE_EX
    cyan = Fore.CYAN
    red = Fore.RED

    def randomToken(self):
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_and_digits) for _ in range(40))

    def randomID(self, length=8):
        return int(''.join(str(random.randint(0, 9)) for _ in range(length)))

    def create_config(self):
        with open('config.json', 'w', encoding='utf-8') as config_file:
            json.dump({
                "Username": "Player",
                "Gold": 99999,
                "Gems": 99999,
                "StarPoints": 99999,
                "Trophies": 0,
                "HighestTrophies": 0,
                "ExperiencePoints": 0,
                "Region": "UA",
                "Environment": "dev",
                "Season": 7,
                "FeaturedBrawler": "Buzz"
            }, config_file, indent=2)
