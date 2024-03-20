#!/usr/bin/env python3

import os
import sys

BASEDIR = os.path.dirname(sys.argv[0])
sys.path.append(BASEDIR + '/../modules')

import infra as I

infra = I.Infrastructure(BASEDIR + '/uc1-infra-1.xml')

print('Node list:')
for node in infra.nodeList:
    print('\tid=\"%s\"' % (node.id))
    print('\t\ttype=\"%s\"' % (node.type))
    for key in node.attr:
        print('\t\t%s=\"%s\"' % (key, node.attr[key]))
