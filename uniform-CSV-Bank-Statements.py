# importing required modules
import calendar
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime

import gspread
import pandas as pd
import wordninja
from dotenv import load_dotenv

"""
Currently, Pandas gives a FutureWarning regarding concatenation of
dataframes with some or all-NA values. It just says to make sure to take out
any NA content (like empty rows) prior to concatenation when the next
release comes out. For now, it prints the warning to terminal and it's ugly.
So let's ignore it.
"""
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


def categorize(data: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize transactions by Description contents.

    Function takes a pandas DataFrame and scans the Description column to
    see in what subcategory the transaction should be placed. Function

    Function also fixes Description strings with wordninja.
    """
    # importing our list of categories
    dirname = os.path.dirname(__file__)
    subcategory_filepath = os.path.join(dirname, "subcategories.json")
    with open(subcategory_filepath, "r", encoding="utf-8") as file:
        categories = json.load(file)

    # iterate through the DataFrame rows and try matching a subcategory
    for row in data.index:
        # remove non-word characters
        desc = data.at[row, "Description"].lower()
        desc = re.sub(r"\W", "", desc)

        # search for a matching subcategory for this description
        for subcategory, text_to_match in categories.items():
            for text in text_to_match:
                # remove non-word characters
                text = text.lower()
                text = re.sub(r"\W", "", text)
                if text in desc:
                    # found a match, adding the subcategory label
                    data.at[row, "SubCategory"] = subcategory
                    break

        # fix specific typos
        desc = re.sub(r"ofrevenmn", "ofrevenumn", desc)
        desc = re.sub(r"loanpymt", "loanpayment", desc)
        desc = re.sub(r"photogphy", "photography", desc)
        desc = re.sub(r"intmtgpay", "intmortgagepay", desc)
        desc = re.sub(r"rerecycllake", "rerecyclelake", desc)
        desc = re.sub(r"nurseacrospay", "nurseacrosspay", desc)

        # replace the description with a nice wordninja'd version
        desc = wordninja.split(desc)
        desc = " ".join(desc)

        # fix specific strings that wordninja parses incorrectly
        desc = re.sub(r"am zn", "amazon", desc)
        desc = re.sub(r"nc sbn", "ncsbn", desc)
        desc = re.sub(r"z elle", "zelle", desc)
        desc = re.sub(r"cost co", "costco", desc)
        desc = re.sub(r"air b nb", "airbnb", desc)
        desc = re.sub(r"air bn b", "airbnb ", desc)
        desc = re.sub(r"lo raine", "loraine", desc)
        desc = re.sub(r"pat re on", "patreon", desc)
        desc = re.sub(r"p at re on", "patreon", desc)
        desc = re.sub(r"tia a bank", "tiaa bank", desc)
        desc = re.sub(r"zw if tinc", "zwift inc", desc)
        desc = re.sub(r"round point", "roundpoint", desc)
        desc = re.sub(r"stra vain cg", "strava inc g", desc)
        desc = re.sub(r"costcow hse", "costco wholesale", desc)
        desc = re.sub(r"goh lever bank", "gohl everbank", desc)

        # get rid of the PREAUTHORIZED part
        desc = re.sub(r"pre[| ]authorized\s(?:credit |debit )*", "", desc)

        # replace old, messy description with pretty, new one
        data.at[row, "Description"] = desc

    return data


def append_dataframe_to_sheet(sheet_key, sheet_name, dataframe):
    """Append dataframe to Google Sheet."""
    # Authenticate with Google Sheets
    gc = gspread.service_account()

    # Open the Google Sheet by Key
    sh = gc.open_by_key(sheet_key)

    # Handle NaN's for JSON
    dataframe = dataframe.fillna("")

    # Select the worksheet by name
    worksheet = sh.worksheet(sheet_name)

    # Convert the DataFrame to a list of lists for easy appending
    values = dataframe.values.tolist()

    # Append the values to the selected range in the worksheet
    worksheet.append_rows(values, "USER_ENTERED", "INSERT_ROWS")


def verify_sheet_existance(sheet_key, years):
    """Verify Google Sheet exists."""
    # Authenticate with Google Sheets
    gc = gspread.service_account()

    # Open the Google Sheet by Key
    sh = gc.open_by_key(sheet_key)
    try:
        for year in years:
            sh.worksheet(year)
    except gspread.exceptions.WorksheetNotFound:
        print(
            f'The sheet, "{year}" does not exist in your workbook.'
            "Please:\n"
            f'\t- Duplicate "{int(year) - 1}"\n'
            "\t- Delete all but the first row\n"
            "\t- Re-run this script\n"
            f"https://docs.google.com/spreadsheets/d/{sheet_key}/edit"
        )
        sys.exit()


# -------------------------------------------------------------------------- #

# a little help text to kick things off
print(
    "\nThis script expects the transaction files in .csv format."
    "\n\n"
    "# -------------------------------------------------------------- #\n"
    "# ------         Bank Transaction File Processor for      ------ #\n"
    "# ------             AMEX, Bremer, TIAA/EverBank          ------ #\n"
    "# -------------------------------------------------------------- #\n"
)

# -------------------------------------------------------------------------- #
load_dotenv()

# initializing master dataframe
columns = {
    "Quarter": "int",
    "Date": "str",
    "Amount": "float",
    "Income": "float",
    "Expense": "float",
    "Category": "str",
    "SubCategory": "str",
    "Description": "str",
    "Year": "int",
    "Month": "str",
    "Month#": "int",
    "CheckNumber": "int",
}
master = pd.DataFrame(columns=columns.keys())
master = master.astype(columns)

while True:
    try:
        # TODO: handle Windows vs Linux
        # specify path to paystub PDF file
        user = (
            os.environ["USERNAME"]
            if sys.platform.startswith("win")
            else os.environ["USER"]
        )
        path = f"/home/{user}/Documents/bank statements/new/"
        completed_folder = f"/home/{user}/Documents/bank statements/completed/"

        statements = os.listdir(path)

        # ensure filenames matching the CSV file produced by this script, and
        # lock files (produced when a file is open in libreoffice) are
        # ignored, and only keep .csv files.
        offender = "I am ready to upload!"
        lock_file = ".~lock."
        csv_ext = ".csv"
        statements = [
            x
            for x in statements
            if offender not in x
            if lock_file not in x
            if csv_ext in x
        ]

        # ensure there is at least one valid statement to process, else quit
        if len(statements) == 0:
            print(
                "\nHey, it does not look like you have any valid .csv "
                f"files in {path}. You will need to download some into "
                "that folder and run this script again."
            )

            sys.exit()
        break
    except FileNotFoundError:
        print(
            f"\nHm... we can't seem to find {path}. Double check that "
            "you selected the correct option. Please try again.\n"
        )
        sys.exit()

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
    date_col = df[df.columns[df.columns.str.contains("Date")]]
    # but make sure to take only the transaction date not the posted date if
    # both exist, as is the case with AMEX.
    if len(date_col.columns) == 2:
        del date_col["Posted Date"]
    # add the date_col to tmp dataframe
    tmp["Date"] = date_col

    # Second, locate the column containing 'description'
    desc_col = df[df.columns[df.columns.str.contains("Description|<Additional Info>")]]
    if len(desc_col.columns) == 2:
        del desc_col["<Description>"]
    # add the desc_col to tmp dataframe
    tmp["Description"] = desc_col

    # Third, locate the column containing 'check number'
    check_col = None
    for column in df.columns:
        if "Check" in column:
            check_col = df[column]
            break
    # Add 'CheckNumber' to tmp dataframe
    tmp["CheckNumber"] = check_col if check_col is not None else None

    # Fourth, locate the column containing 'amount'
    # *note that Bremer has 'withdrawl amount' and 'deposit amount'
    amt_cols = df[df.columns[df.columns.str.contains("Amount")]]
    if len(amt_cols.columns) == 2:
        # this is the case for Bremer where we simply rename the columns
        amt_cols.columns = "Expense Income".split()
        tmp["Income"] = amt_cols["Income"]
        tmp["Expense"] = amt_cols["Expense"].abs()
        tmp["Amount"] = amt_cols["Income"]
        tmp["Amount"] = tmp["Amount"].fillna(amt_cols["Expense"])
    # AMEX, as a credit card, shows purchases as positive numbers, and returns
    # as negative numbers, so let's handle that case.
    elif any(df.columns.str.contains("Appears On Your Statement As")) or any(
        df.columns.str.contains("Card Member")
    ):
        tmp["Income"] = amt_cols[amt_cols < 0].abs()
        tmp["Expense"] = amt_cols[amt_cols >= 0]
        tmp["Amount"] = tmp["Income"]
        tmp.Amount.fillna(-tmp["Expense"], inplace=True)
    # EverBank now uses 'Debits(-)' and 'Credits(+)'
    elif any(df.columns.str.contains("Debits(-)")):
        tmp["Income"] = amt_cols["Credits(+)"]
        # now remove '$-' portion of debit cell contents
        tmp["Expense"] = amt_cols["Debits(-)"]
        tmp["Expense"] = tmp["Expense"].replace({"$-": ""}, regex=True)
        tmp["Amount"] = tmp["Income"]
        tmp.Amount.fillna(-tmp["Expense"], inplace=True)
    else:
        tmp["Amount"] = amt_cols
        tmp["Income"] = amt_cols[amt_cols >= 0]
        tmp["Expense"] = amt_cols[amt_cols < 0].abs()
    # now lets label these rows with 'Income' or 'Expense' as well
    # this may be handy for fine-tuning graphs in Excel or GoogleSheets
    tmp.loc[tmp["Amount"] >= 0, "Category"] = "Income"
    tmp.Category.fillna("Expense", inplace=True)

    print(".", end="")
    # Finally, add tmp to master
    master = pd.concat([master, tmp])

# format Date column to datetime format for subsequent processing
master["Date"] = pd.to_datetime(master["Date"], format="mixed")
# drop rows with missing dates
master = master.dropna(subset=["Date"])
# calculate Quarters
master["Quarter"] = master["Date"].dt.quarter
# calculate Years
master["Year"] = master["Date"].dt.year
# calculate Months
master["Month"] = master["Date"].dt.month.map(lambda x: calendar.month_abbr[x])
master["Month#"] = master["Date"].dt.month
# sort by Date and drop the extra index
master = master.sort_values(by=["Date"]).reset_index(drop=True)
# format the Date how she likes it :)
master["Date"] = master["Date"].dt.strftime("%m/%d/%Y")

# make a DataFrame from master's SubCategory and Description columns
master = categorize(master)

"""
Before we break the strings back into words, let's remove any rows
for credit card payments, as credit card payments are just the sum
owed of money we've already spent on individual purchases. The
individual purchases will all be detailed and covered by the rest of
the data. So we need not bother with seeing numbers for credit card
payments.
"""
card_pymt_rows = master[
    (master["Description"] == "payment thankyou")
    | (master["SubCategory"] == "Credit Card Payments")
].index
master.drop(card_pymt_rows, inplace=True)

# Let's also drop all amounts of $0.00
zeros = master[(master["Amount"] == 0)].index
master.drop(zeros, inplace=True)

# Split dataframe by year
df_list = [d for _, d in master.groupby(["Year"])]

# before moving the files, ensure the destination folder exists or make it
if not os.path.exists(completed_folder):
    os.makedirs(completed_folder)
    print(
        f"\nI made a new folder located at {completed_folder} to "
        "store the bank statements I've finished processing.\n"
    )
# and move the statements to the 'completed' folder
unable_to_move = []
for statement in statements:
    try:
        shutil.move(path + statement, completed_folder)
    except shutil.Error:
        unable_to_move.append(path + statement)

# Stop the clock!
end = time.time()

print(f"\n{master}\n{master.size} cells processed.\n")

# Verify appropriate sheets exist
unique_years: list[int] = list()
for df in df_list:
    unique_years.append(df["Year"].unique())
unique_years = sorted(unique_years)
unique_years = [y for y in unique_years]
verify_sheet_existance(os.getenv("SHEET_KEY"), unique_years)

# Automagically append to Google Sheets
print("Automagically appending data to Google Sheets")
for df in df_list:
    append_dataframe_to_sheet(
        os.getenv("SHEET_KEY"),  # sheet_key
        str(round(df["Year"].mean())),  # sheet_name is the year the data came from
        df,  # dataframe to append
    )

# write out the file file to CSV for uploading to Google Sheets
now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
master.to_csv(path + f"I am ready to upload! {now} ^_^.csv", index=False)
print("ALL DONE! :D", f"Took only {end - start:.3}s to complete")

if len(unable_to_move) > 0:
    print(
        "\nOpe, the following files already exist in the "
        f'"{completed_folder}" folder.\nYou will need to move the file '
        "yourself or just delete it if you're done."
    )
    for file in unable_to_move:
        print(f"\t --> {file}")
