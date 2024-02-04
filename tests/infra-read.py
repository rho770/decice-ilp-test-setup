#!/usr/bin/env python3

import os
import sys

BASEDIR = os.path.dirname(sys.argv[0])
sys.path.append(BASEDIR + '/../modules')

import infra as I

infra = I.Infrastructure(BASEDIR + '/infra-1.xml')

print('Node list:')
for node in infra.nodeList:
    print('\tid=\"%s\"' % (node.id))