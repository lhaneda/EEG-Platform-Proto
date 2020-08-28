import csv

def create_csv(result_file):
    file_basename = 'output.csv'
    result_csv = open(file_basename,'w+')
    result_csv.write('Channel, Band, Function, Value, Start Time, End Time, TS Completed \n')

    for row in result_file:
        row_as_string = str(row)
        result_csv.write(row_as_string[1:-1] + '\n')

    result_csv.close()

    return result_csv
