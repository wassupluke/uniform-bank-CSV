# importing required modules
import calendar
from datetime import datetime
import json
import os
import re
import shutil
import sys
import wordninja
import pandas as pd

# TODO split Amount col into Income and Expense cols
# see https://sparkbyexamples.com/pandas/split-pandas-dataframe-by-column-value/


def check_user() -> str:
    while True:
        try:
            user = input(
                    'First, let me know who\'s computer is running the '
                    'script.\n(1): Luke, or (2): Alyssa  '
                    )
            user = int(user)
            if user == 1:
                return 'wassu'
            if user == 2:
                return 'alyssawass'
            raise Exception(f'"{user}" wasn\'t an option. Try again.')
        except ValueError:
            print(
                '\nThat didn\'t look like a valid number. Please try again, '
                'or reach out to Luke for assistance getting this to run.\n'
                )
        except Exception as e:
            print(f'\n{e.args[0]}\n')


def categorize(df: object) -> object:
    # Function takes a pandas DataFrame and scans the Description column to
    # see in what category the transaction should be placed. Function returns
    # an updated DataFrame complete with categorized transactions.
    # Function also fixes Description strings with wordninja.

    # importing our list of categories
    with open('categories.json', 'r') as file:
        categories = json.load(file)

    # iterate through the DataFrame rows and try matching a category
    for row in df.index:
        # remove non-word characters
        desc = df.at[row, 'Description'].lower()
        desc = re.sub(r'\W', '', desc)

        # search for a matching category for this description
        for category, text_to_match in categories.items():
            for text in text_to_match:
                # remove non-word characters
                text = text.lower()
                text = re.sub(r'\W', '', text)
                if text in desc:
                    # found a match, adding the category label
                    df.at[row, 'Category'] = category
                    break

        # fix specific typos
        desc = re.sub(r'ofrevenmn', 'ofrevenumn', desc)
        desc = re.sub(r'loanpymt', 'loanpayment', desc)
        desc = re.sub(r'photogphy', 'photography', desc)
        desc = re.sub(r'intmtgpay', 'intmortgagepay', desc)
        desc = re.sub(r'rerecycllake', 'rerecyclelake', desc)
        desc = re.sub(r'nurseacrospay', 'nurseacrosspay', desc)

        # replace the description with a nice wordninja'd version
        desc = wordninja.split(desc)
        desc = ' '.join(desc)

        # fix specific strings that wordninja parses incorrectly
        desc = re.sub(r'am zn', 'amazon', desc)
        desc = re.sub(r'nc sbn', 'ncsbn', desc)
        desc = re.sub(r'z elle', 'zelle', desc)
        desc = re.sub(r'cost co', 'costco', desc)
        desc = re.sub(r'air b nb', 'airbnb', desc)
        desc = re.sub(r'lo raine', 'loraine', desc)
        desc = re.sub(r'pat re on', 'patreon', desc)
        desc = re.sub(r'p at re on', 'patreon', desc)
        desc = re.sub(r'tia a bank', 'tiaa bank', desc)
        desc = re.sub(r'zw if tinc', 'zwift inc', desc)
        desc = re.sub(r'round point', 'roundpoint', desc)
        desc = re.sub(r'stra vain cg', 'strava inc g', desc)
        desc = re.sub(r'costcow hse', 'costco wholesale', desc)
        desc = re.sub(r'goh lever bank', 'gohl everbank', desc)

        # get rid of the PREAUTHORIZED part
        desc = re.sub(r'preauthorized\s(?:credit |debit )*', '', desc)

        # replace old, messy description with pretty, new one
        df.at[row, 'Description'] = desc

    return df


def save_to_sheet(name, minutes, row) -> None:
    # Function pulled from BMS Challenges script, uploads data to GoogleSheets

    # Open the spreadsheet and the first sheet
    path = 'assets/pygsheets_integration_service_key.json'
    gc = pygsheets.authorize(service_account_file=path)
    sh = gc.open("BMS IRL Challenges")
    wks = sh.sheet1

    wks.update_value('B' + str(row), name.capitalize())
    wks.update_value('C' + str(row), minutes)

    # Adds timestamp on spreadsheet
    dtn = datetime.now()
    now = (
            f"{dtn.month}/{dtn.day}/{dtn.year} at "
            "{dtn.hour}:{dtn.minute:02d} CST"
            )
    wks.update_value('B44', now)


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

# initializing master dataframe
columns = {
        'Quarter': 'int', 'Date': 'str',
        'Amount': 'float', 'Category': 'str',
        'Description': 'str', 'Year': 'int',
        'Month': 'str', 'CheckNumber': 'int'
        }
master = pd.DataFrame(columns=columns.keys())
master = master.astype(columns)

while True:
    try:
        # Let's make this work nicely for different users
        user = check_user()

        # specify path to paystub PDF file
        path = f'/home/{user}/Documents/bank statements/new/'
        completed_folder = f'/home/{user}/Documents/bank statements/completed/'

        statements = os.listdir(path)

        # ensure filenames matching the CSV file produced
        # by this script are ignored
        offender = 'I am ready to upload!'
        csv_ext = '.csv'
        statements = [
                x for x in statements if offender not in x if csv_ext in x
                ]

        # ensure there is at least one valid statement to process, else quit
        if len(statements) == 0:
            print(
                    '\nHey, it does not look like you have any valid .csv '
                    f'files in {path}. You will need to download some into '
                    'that folder and run this script again.'
                    )

            sys.exit()
        break
    except FileNotFoundError:
        print(
                f'\nHm... we can\'t seem to find {path}. Double check that '
                'you selected the correct option. Please try again.\n'
                )


for statement in statements:
    # initalize a temporary dataframe
    tmp = pd.DataFrame(columns=columns.keys())
    tmp = tmp.astype(columns)

    # create Pandas dataframe from statement
    statement = os.path.join(path, statement)
    df = pd.read_csv(statement)

    # Firstly, locate the column containing 'date'
    date_col = df[df.columns[df.columns.str.contains('Date')]]
    # add the date_col to tmp dataframe
    tmp['Date'] = date_col

    # Second, locate the column containing 'description'
    desc_col = df[df.columns[df.columns.str.contains(
        'Description|<Additional Info>'
        )]]
    if len(desc_col.columns) == 2:
        del desc_col['<Description>']
    # add the desc_col to tmp dataframe
    tmp['Description'] = desc_col

    # Third, locate the column containing 'check number'
    check_col = None
    for column in df.columns:
        if 'Check' in column:
            check_col = df[column]
            break
    # Add 'CheckNumber' to tmp dataframe
    tmp['CheckNumber'] = check_col if check_col is not None else None

    # Fourth, locate the column containing 'amount'
    # *note that Bremer has 'withdrawl amount' and 'deposit amount'
    amt_col = df[df.columns[df.columns.str.contains('Amount')]]
    if len(amt_col.columns) == 2:
        # this is the case for Bremer where we need to combine the columns
        # first let's name both columns
        amt_col.columns = 'Amount Deposit'.split()
        # now let's fill blanks in the Amount column with values from Deposit
        amt_col.Amount.fillna(amt_col.Deposit, inplace=True)
        # we don't need the Deposit column anymore, so delete it
        del amt_col['Deposit']
    tmp['Amount'] = amt_col
    # Finally, add tmp to master
    master = pd.concat([master, tmp])

    # before moving the file, ensure the destination folder exists or make it
    if not os.path.exists(completed_folder):
        os.makedirs(completed_folder)
        print(
                f'\nI made a new folder located at {completed_folder} to '
                'store the bank statements I\'ve finished processing.\n'
                )
    # and move the statement to the 'completed' folder
    print('.', end='')
    shutil.move(statement, completed_folder)

# format Date column to datetime format for subsequent processing
master['Date'] = pd.to_datetime(master['Date'], format='mixed')
# drop rows with missing dates
master = master.dropna(subset=['Date'])
# calculate Quarters
master['Quarter'] = master['Date'].dt.quarter
# calculate Years
master['Year'] = master['Date'].dt.year
# calculate Months
master['Month'] = master['Date'].dt.month.map(lambda x: calendar.month_abbr[x])
# sort by Date and drop the extra index
master = master.sort_values(by=['Date']).reset_index(drop=True)
# format the Date how she likes it :)
master['Date'] = master['Date'].dt.strftime('%m/%d/%Y')

# make a DataFrame from master's Category and Description columns
master = categorize(master)

print(f'\n{master}\n{master.size} cells processed.\n')

# write out the file file to CSV for uploading to Google Sheets
now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
master.to_csv(path + f'I am ready to upload! {now} ^_^.csv', index=False)
print('ALL DONE! :D')
