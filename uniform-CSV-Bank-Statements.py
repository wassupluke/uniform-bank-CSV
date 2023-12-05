# importing required modules
import csv
import os

# TODO move statement from 'new' folder to 'completed'


def identify_bank(statement: str) -> str:
    if 'tiaa' in statement.lower():
        return 'TIAA'
    elif 'bremer' in statement.lower():
        return 'Bremer'
    elif 'amex' in statement.lower():
        return 'AMEX'
    else:
        return 'No bank was identified. Check your file names.'


def cleanTIAA(path: str, statement: str) -> str:
    statement = os.path.join(path, statement)

    # initializing the titles and rows list
    fields, rows = [], []

    # reading csv file
    with open(statement, 'r') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting field names through first row if row not empty
        while len(next(csvreader)) == 0:
            next(csvreader)
        fields = next(csvreader)

        [rows.append(row) for row in csvreader]
    return fields, rows


# -------------------------------------------------------------------------- #

# a little help text to kick things off
print(
        '\nThis script expects the statements to contain one of the following '
        'bits of text in order to correctly identify the bank from which it '
        'came. It is case-insensitive.\n'
        )

# specify path to paystub PDF files
path = '/home/alyssawass/Documents/bank statements/new'
statements = os.listdir(path)

try:
    banks = [identify_bank(statement) for statement in statements]
    bank_statement_dict = {}
    
except:
    print('Well that failed miserably.')

print(banks)
