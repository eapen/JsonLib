#!/usr/bin/env python

import cgi
import json
import os

form = cgi.FieldStorage()

def output(data):
  if form.has_key('callback'):
    out = '%s(%s)\n' % (form.getfirst('callback'), json.dumps(data))
  else:
    out = '%s\n' % json.dumps(data)
  print "Content-Type: text/javascript"
  print "Content-Length: %d" % len(out)
  print
  print out

result = {}

bytes = 256
try:
  bytes = int(form.getfirst('bytes', '256'))
except:
  pass
format = form.getfirst('format', 'string')

if format == 'array':
  output({'urandom': [ord(c) for c in os.urandom(bytes)]})
else:
  output({'urandom': unicode(os.urandom(bytes), 'iso-8859-1')})
