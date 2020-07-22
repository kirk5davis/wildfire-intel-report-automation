"""
    sitecustomize.py 
    ================

    To ensure that the WKHTMLTOPDF/PDFKit binaries are found by the script
    - these must be added to the beginning of your path variables.  

    - to use this, simply import into script that will run, trust me Josh...

"""
import os

# insert the GTK3 Runtime folder at the beginning
PDFKIT_REQ_FOLDER = r"C:\Program Files\wkhtmltopdf\bin"
os.environ['PATH'] = PDFKIT_REQ_FOLDER + os.pathsep + os.environ.get('PATH', '')
