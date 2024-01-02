# Currently, Pandas gives a FutureWarning regarding concatenation of
# dataframes with some or all-NA values. It just says to make sure to take out
# any NA content (like empty rows) prior to concatenation when the next
# release comes out. For now, it prints the warning to terminal and it's ugly.
# So let's ignore it.
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# importing required modules
import calendar
from datetime import datetime
import json
import os
import re
import shutil
import sys
import time
import wordninja
import pandas as pd


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
    # see in what subcategory the transaction should be placed. Function
    # returns an updated DataFrame complete with categorized transactions.
    # Function also fixes Description strings with wordninja.

    # importing our list of categories
    dirname = os.path.dirname(__file__)
    subcategory_filepath = os.path.join(dirname, 'subcategories.json')
    with open(subcategory_filepath, 'r', encoding='utf-8') as file:
        categories = json.load(file)

    # iterate through the DataFrame rows and try matching a subcategory
    for row in df.index:
        # remove non-word characters
        desc = df.at[row, 'Description'].lower()
        desc = re.sub(r'\W', '', desc)

        # search for a matching subcategory for this description
        for subcategory, text_to_match in categories.items():
            for text in text_to_match:
                # remove non-word characters
                text = text.lower()
                text = re.sub(r'\W', '', text)
                if text in desc:
                    # found a match, adding the subcategory label
                    df.at[row, 'SubCategory'] = subcategory
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
        desc = re.sub(r'air bn b', 'airbnb ', desc)
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
        desc = re.sub(r'pre[| ]authorized\s(?:credit |debit )*', '', desc)

        # replace old, messy description with pretty, new one
        df.at[row, 'Description'] = desc

    return df


# -------------------------------------------------------------------------- #

# a little help text to kick things off
print(
        '\nThis script expects the transaction files in .csv format.'
        '\n\n'
        '# -------------------------------------------------------------- #\n'
        '# ------         Bank Transaction File Processor for      ------ #\n'
        '# ------           AMEX, Bremer, TIAA, or EverBank        ------ #\n'
        '# -------------------------------------------------------------- #\n'
        )

# -------------------------------------------------------------------------- #

# initializing master dataframe
columns = {
        'Quarter': 'int',
        'Date': 'str',
        'Amount': 'float',
        'Income': 'float',
        'Expense': 'float',
        'Category': 'str',
        'SubCategory': 'str',
        'Description': 'str',
        'Year': 'int',
        'Month': 'str',
        'Month#': 'int',
        'CheckNumber': 'int'
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

        # ensure filenames matching the CSV file produced by this script, and
        # lock files (produced when a file is open in libreoffice) are
        # ignored, and only keep .csv files.
        offender = 'I am ready to upload!'
        lock_file = '.~lock.'
        csv_ext = '.csv'
        statements = [
                x for x in statements\
                    if offender not in x\
                    if lock_file not in x\
                    if csv_ext in x
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

# Start the timer, let's see how fast this baby runs!
start = time.time()

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
    amt_cols = df[df.columns[df.columns.str.contains('Amount')]]
    if len(amt_cols.columns) == 2:
        # this is the case for Bremer where we simply rename the columns
        amt_cols.columns = 'Expense Income'.split()
        tmp['Income'] = amt_cols['Income']
        tmp['Amount'] = amt_cols['Income']
        tmp['Amount'] = tmp['Amount'].fillna(amt_cols['Expense'], inplace=True)
        tmp['Expense'] = amt_cols['Expense'].abs()
    # AMEX, as a credit card, shows purchases as positive numbers, and returns
    # as negative numbers, so let's handle that case.
    elif any(df.columns.str.contains('Appears On Your Statement As')):
        tmp['Income'] = amt_cols[amt_cols < 0].abs()
        tmp['Expense'] = amt_cols[amt_cols >= 0]
        tmp['Amount'] = tmp['Income']
        tmp.Amount.fillna(-tmp['Expense'], inplace=True)
    else:
        tmp['Amount'] = amt_cols
        tmp['Income'] = amt_cols[amt_cols >= 0]
        tmp['Expense'] = amt_cols[amt_cols < 0].abs()
    # now lets label these rows with 'Income' or 'Expense' as well
    # this may be handy for fine-tuning graphs in Excel or GoogleSheets
    tmp.loc[tmp['Amount'] >= 0, 'Category'] = 'Income'
    tmp.Category.fillna('Expense', inplace=True)

    print('.', end='')
    # Finally, add tmp to master
    master = pd.concat([master, tmp])

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
master['Month#'] = master['Date'].dt.month
# sort by Date and drop the extra index
master = master.sort_values(by=['Date']).reset_index(drop=True)
# format the Date how she likes it :)
master['Date'] = master['Date'].dt.strftime('%m/%d/%Y')

# make a DataFrame from master's SubCategory and Description columns
master = categorize(master)

# Before we break the strings back into words, let's remove any rows
# for credit card payments, as credit card payments are just the sum
# owed of money we've already spent on individual purchases. The
# individual purchases will all be detailed and covered by the rest of
# the data. So we need not bother with seeing numbers for credit card
# payments.
card_pymt_rows = master[
        (master['Description'] == 'payment thankyou') |
        (master['SubCategory'] == 'Credit Card Payments')
        ].index
master.drop(card_pymt_rows, inplace=True)

# Let's also drop all amounts of $0.00
zeros = master[(master['Amount'] == 0)].index
master.drop(zeros, inplace=True)

# before moving the files, ensure the destination folder exists or make it
if not os.path.exists(completed_folder):
    os.makedirs(completed_folder)
    print(
            f'\nI made a new folder located at {completed_folder} to '
            'store the bank statements I\'ve finished processing.\n'
            )
# and move the statements to the 'completed' folder
unable_to_move = []
for statement in statements:
    try:
        shutil.move(statement, completed_folder)
    except shutil.Error:
        unable_to_move.append(statement)

# Stop the clock!
end = time.time()

print(f'\n{master}\n{master.size} cells processed.\n')

# write out the file file to CSV for uploading to Google Sheets
now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
master.to_csv(path + f'I am ready to upload! {now} ^_^.csv', index=False)
print('ALL DONE! :D', f'Took only {end - start:.3}s to complete')

if len(unable_to_move) > 0:
    print(
            '\nOpe, the following files already exist in the '
            f'"{completed_folder}" folder.\nYou will need to move the file '
            'yourself or just delete it if you\'re done.'
        )
    for file in unable_to_move:
        print(f'\t --> {file}')

