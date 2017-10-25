Overview of the folder :

------------Every specificity of the software is detailed in the softwareUserManual.pdf file---------------------


- CLK=40MHz_OUTPUT=1500MHZ_SPACING=40kHz.txt : text file containing specific
settings that can be loaded from the application with the "Load button".

- createExecutable.txt : memo explaining how to create a .exe file from a Python
script using Pyinstaller.

- Int_Graph_PLL.py : Python file containing the source code of the application.
To open it, right click on the file and select "Edit with IDLE" (Python 2.7
must be installed on the computer, to do so see : https://www.python.org/downloads/).
Python's IDLE then opens and displays the source code.
To run the software, go in the "Run" tab and select "Run Module" (or press F5).
Debug messages may be displayed in the Python Shell.

- PLL_Controller_version-0.1.exe : executable stand alone .exe file that launches
the application simply by double-clicking on the file.
No debug message will be displayed while the software is used.

- PLLControllerLogo.ico : icon file containing the application's logo. This icon
is used when generating a .exe file using Pyinstaller (see createExecutable.txt
file).

- softwareUserManual.pdf : document explaining everything there is to know about
the PLL Controller application.