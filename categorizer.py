import pandas as pd
import timeit
from categories import categories

def categorize(df: object) -> object:
    for row in df.index:
        description = df['Description'][row]

        for category, text_to_match in categories.items():
            for text in text_to_match:
                if text in description.lower():
                    # add category to category column at particular row
                    df['Category'][row] = category
                    print(category)
                    break
                else:
                    pass
            break
    return df

'''
#    -----------------------------------------

    # element exists in listof listor not?
    timeit.timeit(res1 = elem in (item for sublist in ini_list for item in sublist), number=10000)
    res2 = elem1 in (item for sublist in ini_list for item in sublist)
 
    # printing result
    print(str(res1), "\n", str(res2))

#    -----------------------------------------

    # element exists in listof listor not?
    res1 = elem_to_find in chain(*ini_list)
    res2 = elem_to_find1 in chain(*ini_list)
 
    # printing result
    print(str(res1), "\n", str(res2))

#    -----------------------------------------

    # element exists in listof list or not?
    res1 = functools.reduce(lambda x, y: x or y, [elem_to_find in sublist for sublist in ini_list])
    res2 = functools.reduce(lambda x, y: x or y, [elem_to_find1 in sublist for sublist in ini_list])
 
    # printing result
    print(res1)
    print(res2)
'''


path_to_master = '/home/wassu/Documents/bank statements/new/I am ready to upload! 12-10-2023 11:52:01 ^_^.csv'
master = pd.read_csv(path_to_master)

cat_desc_cols = master[['Category', 'Description']]

cat_desc_cols = categorize(cat_desc_cols)

print(cat_desc_cols.to_string())
