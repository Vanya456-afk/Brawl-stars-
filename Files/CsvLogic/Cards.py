from Files.CsvReader import CsvReader

class Cards:
    def get_spg_id(self):
        rows = CsvReader().readCsv('GameAssets/csv_logic/cards.csv')
        return [rows.index(row) for row in rows if len(row) > 7 and row[7].lower() in ('4', '5')]

    def check_spg_id(self, id):
        rows = CsvReader().readCsv('GameAssets/csv_logic/cards.csv')
        for row in rows:
            if rows.index(row) == id:
                return row[7].lower()
        return None

    def get_brawler_unlock(self):
        rows = CsvReader().readCsv('GameAssets/csv_logic/cards.csv')
        return [rows.index(row) for row in rows if len(row) > 7 and row[7].lower() == '0']

    def get_spg_by_brawler_id(self, brawler_id, type):
        chars = CsvReader().readCsv('GameAssets/csv_logic/characters.csv')
        cards = CsvReader().readCsv('GameAssets/csv_logic/cards.csv')
        if brawler_id >= len(chars):
            return None
        name = chars[brawler_id][0]
        for row in cards:
            if len(row) > 7 and row[3] == name and row[7].lower() == str(type):
                return cards.index(row)
        return None

    def get_unlock_by_brawler_id(self, brawler_id):
        chars = CsvReader().readCsv('GameAssets/csv_logic/characters.csv')
        cards = CsvReader().readCsv('GameAssets/csv_logic/cards.csv')
        if brawler_id >= len(chars):
            return None
        name = chars[brawler_id][0]
        for row in cards:
            if len(row) > 7 and row[7].lower() == '0' and row[3] == name:
                return cards.index(row)
        return None
