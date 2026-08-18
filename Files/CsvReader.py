import csv

class CsvReader:
    def readCsv(self, filename):
        rowData = []
        with open(filename, encoding='utf-8') as csvFile:
            reader = csv.reader(csvFile, delimiter=',')
            for line_count, row in enumerate(reader):
                if line_count >= 2:
                    rowData.append(row)
        return rowData
