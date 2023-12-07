# importing required modules
import csv
import os
import pandas as pd

# TODO move statement from 'new' folder to 'completed'
# TODO columns she wants: Date, CheckNumber, VerboseDescription, Amount
# TODO additional columns from python: Year, Quarter, Month, Category
#         0       1      2       3               4           5      6     7
# TODO Quarter, Date, Amount, Category, VerboseDescription, Year, Month,Check#

# if 'date' -> set as Quarter[0], Date[1], Year[5], Month[6] column[index]
# if 'amount' -> condense to single comlumn (bc bremer didn't play nicely)
# if 'amount' -> set as Amount[2]
# if '<additional info>' or 'description' -> set that as Description[4] column
# if 'check' -> set as CheckNumber[7] or pass (AMEX doesn't have check nums)


def check_user() -> str:
    while True:
        try:
            user = input(
                    'First, let me know who\'s computer is running the '
                    'script.\n(1): Luke, or (2): Alyssa  '
                    )
            user = int(user)
            if user == 1:
                user = 'wassu'
            elif user == 2:
                user = 'alyssawass'
            else:
                raise Exception(f'"{user}" wasn\'t an option. Try again.')
            return user
        except ValueError:
            print(
                '\nThat didn\'t look like a valid number. Please try again, or '
                'reach out to Luke for assistance getting this to run.\n'
                )
        except Exception as e:
            print(f'\n{e.args[0]}\n')


def organize(statement) -> list[list]:
    # Function takes a statement and returns my custom set of select rows

    # initializing the titles and rows list
    fields, rows = [], []

    with open(statement, 'r') as csvfile:
        # reading csv file
        csvreader = csv.reader(csvfile)
        # extracting field names through first row if row not empty
        while len(next(csvreader)) == 0:
            next(csvreader)
        fields = next(csvreader)

        [rows.append(row) for row in csvreader]
        return rows


def finalize_csv():
    outfile = 'csv-done.csv' 
    with open(outfile, 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
     
        # writing the fields
        csvwriter.writerow(fields)
     
        # writing the data rows
        csvwriter.writerows(rows)

# -------------------------------------------------------------------------- #

# a little help text to kick things off
print(
        '\nThis script expects the statements to contain one of the '
        'following bits of text in order to correctly identify the bank from '
        'which it came. It is case-insensitive.\n\n'
        '# -------------------------------------------------------------- #\n'
        '# ------           AMEX, Bremer, TIAA, or EverBank        ------ #\n'
        '# -------------------------------------------------------------- #\n'
        )

# -------------------------------------------------------------------------- #

# initializing lists
fields = [
        'Quarter', 'Date', 'Amount', 'Category', 'VerboseDescription', 'Year',
        'Month, CheckNumber'
        ]
rows = []

# Let's make this work nicely for different users
user = check_user()

# specify path to paystub PDF file
path = f'/home/{user}/Documents/bank statements/new'

statements = os.listdir(path)

for statement in statements:
    # Luke's default way
    statement = os.path.join(path, statement)
    organize(statement)
    # the Pandas way
    df = pd.read_csv(statement)
    print(df.columns)
    for i in df.columns:
        if '<' in i:
            print('need to .combine() some columns for Withdrawl Amount'
                  'and Deposit Amount to make this work')
            # See https://www.w3schools.com/python/pandas/trypython.asp?filename=demo_ref_df_combine

    # add a custom column called 'Quarter'
    # df = df.assign(Quarter = ["Emil", "Tobias", "Linus"])

    # Finally, use df.append() to append this new dataframe to the main
    # dataframe.
    '''
    data1 = {
  "age": [16, 14, 10],
  "qualified": [True, True, True]
}
df1 = pd.DataFrame(data1)

data2 = {
  "age": [55, 40],
  "qualified": [True, False]
}
df2 = pd.DataFrame(data2)

newdf = df1.append(df2)
'''

