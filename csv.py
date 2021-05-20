import csv
import io
def create_csv(column_names, data):
    input = [column_names] + data
    csvfile = io.StringIO()
    csvwriter = csv.writer(csvfile)
    for i in input:
        csvwriter.writerow(i)
    return csvfile