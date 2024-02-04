#!/usr/bin/env python3

import os
import sys

BASEDIR = os.path.dirname(sys.argv[0])
sys.path.append(BASEDIR + '/../modules')

import appl as A

appl = A.Application(BASEDIR + '/appl-1.xml')

print('Container list:')
for container in appl.containerList:
    print('\tid=\"%s\"' % (container.id))