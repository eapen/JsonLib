#!/usr/bin/env python

import cgi
import json
import os
import time

def output(data):
  if 'callback' in cgi.FieldStorage().keys():
    out = '%s(%s)\n' % (cgi.FieldStorage().getfirst('callback'),
                        json.dumps(data))
  else:
    out = '%s\n' % json.dumps(data)
  print "Content-Type: text/javascript"
  print "Content-Length: %d" % len(out)
  print
  print out

output({'time' : time.time()})
