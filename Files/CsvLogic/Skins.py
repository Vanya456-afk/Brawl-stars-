from Files.CsvReader import CsvReader

class Skins:
    def get_skins_id(self):
        rows = CsvReader().readCsv('GameAssets/csv_logic/skins.csv')
        return list(range(len(rows)))
