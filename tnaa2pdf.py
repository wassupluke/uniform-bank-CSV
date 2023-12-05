# importing required modules
import os
import PyPDF2


def print_paystub(path, paystub):
    paystub = os.path.join(path, paystub)
    pdfFileObj = open(paystub, 'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    total_pages = f'\n{paystub} has {len(pdfReader.pages)} pages.\n'
    content = [page.extract_text() for page in pdfReader.pages]
    content = ' '.join(content)
    pdfFileObj.close()
    return total_pages + content


# -------------------------------------------------------------------------- #

# specify path to paystub PDF files
path = '/home/alyssawass/Documents/paystubs/'
paystubs = os.listdir(path)

for paystub in paystubs:
    print(print_paystub(path, paystub))
