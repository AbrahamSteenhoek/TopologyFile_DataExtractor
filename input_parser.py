import os
import argparse
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def ParseInputArgs():
    parser = argparse.ArgumentParser( description='Calculate the distance between two components in a topology file' )
    parser.add_argument( '-n', '--net', help='XNet (assuming topology file is named after Xnet) containing the start and end nodes', type=str, required=True )
    parser.add_argument( '-s', '--start', help='Start of the path', type=str, required=True )
    parser.add_argument( '-e', '--end', help='End of the path', type=str, required=True )
    args = parser.parse_args()
    return args.net, args.start, args.end

def BrowseFile() -> str:
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    # print( os.getcwd() )
    filename = askopenfilename( initialdir = f'{os.getcwd()}/tops', title = 'Select Netlist File') # show an "Open" dialog box and return the path to the selected file
    print('filename: ' + filename)
    if not filename: # quit if no file was selected
        print( 'No file selected. Quitting...' )
        quit()
    return filename

# ParseInput()
