from Files.CsvReader import CsvReader

class Characters:
    def get_brawlers_id(self):
        brawlers_id = []
        row_data = CsvReader().readCsv('GameAssets/csv_logic/characters.csv')
        for row in row_data:
            if len(row) > 22 and row[22] == 'Hero' and row[2].lower() != 'true' and row[1].lower() != 'true':
                brawlers_id.append(row_data.index(row))
        return brawlers_id

    def get_brawler_by_skin_id(self, skin_id):
        chars = CsvReader().readCsv('GameAssets/csv_logic/characters.csv')
        skins = CsvReader().readCsv('GameAssets/csv_logic/skins.csv')
        configs = CsvReader().readCsv('GameAssets/csv_logic/skin_confs.csv')
        for row in skins:
            if skins.index(row) == skin_id:
                conf = row[1]
                for cfg in configs:
                    if cfg[0] == conf:
                        for char in chars:
                            if char[0] == cfg[1]:
                                return chars.index(char)
        return None
