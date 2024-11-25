# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 18:32:41 2024

@author: Francesco Brandoli
"""

import subprocess
    
generate_xml = subprocess.run(["python", "../modules/xml_generator.py"], capture_output=True, text=True)
run_main = subprocess.run(["python", "test_main.py"], capture_output=True, text=True)

    
