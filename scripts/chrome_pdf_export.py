import subprocess32 as subprocess
import sys

class ChromePDF(object):

    # set headless chrome arguments
    _chrome_args = (
        '{chrome_exec}',
        '--headless',
        '--disable-gpu',
        '--window-size=900,900',
        '--no-margins',
        #'--run-all-compositor-stages-before-draw',
        #'--virtual-time-budget=10000',
        #'--webkit-print-color-adjust=exact',
        '--print-to-pdf={output_file}',
        '{input_file}'
    )

    def __init__(self,chrome_exec):
        '''
        Constructor
        chrome_exec (string) - path to chrome executable
        '''

        # check if the chrome executable path is non-empty string
        assert isinstance(chrome_exec,str) and chrome_exec != ''

        self._chrome_exe = chrome_exec

        
    def html_to_pdf(self,input_html_file, output_file):
        '''
        Converts the given html_byte_string to PDF stored at output_file

        html_byte_string (string) - html to be rendered to PDF
        output_file (string) - file object to output PDF file  

        returns True if successful and False otherwise 
        '''

        # prepare the shell command
        print_to_pdf_command = ' '.join(self._chrome_args).format(
                chrome_exec=self._chrome_exe,
                input_file=input_html_file,
                output_file=output_file.name
            )

        isNotWindows = not sys.platform.startswith('win32')

        try:
            # execute the shell command to generate PDF
            subprocess.run(print_to_pdf_command,shell=isNotWindows,check=True)
        except subprocess.CalledProcessError:
            return False
        
        return True