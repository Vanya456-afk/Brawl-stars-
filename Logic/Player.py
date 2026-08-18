import json
from Utils.Helpers import Helpers
from Files.CsvLogic.Characters import Characters
from Files.CsvLogic.Skins import Skins
from Files.CsvLogic.Cards import Cards

class Player:
    try:
        with open('config.json', 'r', encoding='utf-8') as config:
            content = config.read()
    except FileNotFoundError:
        Helpers().create_config()
        with open('config.json', 'r', encoding='utf-8') as config:
            content = config.read()

    settings = json.loads(content)
    skins_id = Skins().get_skins_id()
    brawlers_id = Characters().get_brawlers_id()
    ID = 0
    token = 'SomeRandomToken'
    name = settings['Username']
    profile_icon = settings['Thumbnail']
    name_color = settings['NameColor']
    trophies = settings['Trophies']
    high_trophies = settings['HighestTrophies']
    trophy_reward = settings['TrophyRoadReward']
    exp_points = settings['ExperiencePoints']
    gems = settings['Gems']
    resources = [{'ID': 1, 'Amount': settings['BrawlBoxTokens']}, {'ID': 8, 'Amount': settings['Gold']}, {'ID': 9, 'Amount': settings['BigBoxTokens']}, {'ID': 10, 'Amount': settings['StarPoints']}]
    region = settings['Region']
    content_creator = settings['SupportedContentCreator']
    home_brawler = settings['HomeBrawler']
    theme_id = settings['ThemeID']
    environment = settings['Environment']
    db = None
    unlocked_skins = skins_id
    brawlers_unlocked = brawlers_id
    brawlers_card_id = [Cards().get_unlock_by_brawler_id(x) for x in brawlers_unlocked]
    brawlers_spg = Cards().get_spg_id()
    def_trophies = settings['BrawlersTrophies']
    def_high_trophies = settings['BrawlersHighestTrophies']
    brawlers_trophies = {str(x): def_trophies for x in brawlers_id}
    brawlers_high_trophies = {str(x): def_high_trophies for x in brawlers_id}
    def_level = settings['BrawlersLevel'] - 1
    brawlers_level = {str(x): def_level for x in brawlers_id}
    def_pp = settings['BrawlersPowerPoints']
    brawlers_powerpoints = {str(x): def_pp for x in brawlers_id}
    clients = {}

    def __init__(self, device):
        self.device = device
