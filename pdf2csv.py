# importing required modules
import os
import PyPDF2


def print_paystub(path: str, paystub: str) -> str:
    paystub = os.path.join(path, paystub)
    pdfFileObj = open(paystub, 'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    content = [page.extract_text() for page in pdfReader.pages]
    content = ' '.join(content)
    total_pages = f'\n{paystub} had {len(pdfReader.pages)} pages.\n'
    pdfFileObj.close()
    return content + total_pages


def tnaa_pdf2csv():
    ...


def mayo_pdf2csv():
    ...


# -------------------------------------------------------------------------- #

# specify path to paystub PDF files
path = '/home/alyssawass/Documents/paystubs/'
paystubs = os.listdir(path)

for paystub in paystubs:
    content = print_paystub(path, paystub)
    print(content)
    content = content.split('\n')
    content = [line.strip() for line in content if line != '']
