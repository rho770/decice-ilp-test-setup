# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 17:55:58 2024

@author: Francesco Brandoli
"""
import sys

def print_to_file(output_file, message):

    with open(output_file, "a") as file:
        file.write(message + "\n")
        
def overwrite_file(output_file):
    """
    Overwrite the file at the start of the script execution.
    This ensures the file is cleared each time the script is rerun.
    """
    with open(output_file, 'w') as file:
        # HEADER
        file.write("DECICE - DEVICE-EDGE-CLOUD INTELLIGENT COLLABORATION FRAMEWORK\n") 





