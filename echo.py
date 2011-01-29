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
for key in form.keys():
  if key != 'callback':
    if form[key].filename:
      result[key + " filename"] = form[key].filename
for key in form.keys():
  if key != 'callback':
    result[key] = form[key].value

output(result)
