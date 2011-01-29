#!/usr/bin/env python

import cgitb
cgitb.enable()
import cgi
import json
import os
import urllib2
import sys
import re
import chardet
import codecs
import urlparse
import soupselect
from ordereddict import OrderedDict
from BeautifulSoup import BeautifulSoup

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

def striptag(tag):
  texts = tag.findAll(text=True)
  def visible(element):
    if element.parent.name == '[document]':
      return False
    elif re.match('<!--.*-->', str(element)):
      return False
    return True
  return filter(visible, texts)

def stripinvisible(tag):
  texts = tag.findAll(text=True)
  def visible(element):
    if element.parent.name in ['[document]', 'script', 'style', 'title']:
      return False
    elif re.match('<!--.*-->', str(element)):
      return False
    return True
  return filter(visible, texts)

def dictify(tag):
  return OrderedDict(
    [ ('tag', tag.name) ] +
    [ ('attr_' + attr, value) for attr, value in tag.attrs ] +
    [ ('text', u''.join(striptag(tag))) ])

form = cgi.FieldStorage()
url = form.getfirst('url')
data = form.getfirst('data')
request_headers = sum([h.split('\n') for h in form.getlist('header')], [])
select = form.getfirst('select')
extract = form.getfirst('extract')
requested_encoding = form.getfirst('encoding')
user_agent = os.environ.get("HTTP_USER_AGENT", None)

if url is None:
  output({'error': 'url argument required'})
  sys.exit(0)

urlhost = urlparse.urlparse(url).hostname
if urlhost in ['jsonlib.appspot.com', 'jsonlib.com',
               'call.jsonlib.com', 'www.jsonlib.com']:
  output({'error': 'very clever - no'})
  sys.exit(0)

try:
  # For security, specify supported protocols explicitly, i.e.,
  # please do not provide support for file:// protocol!
  opener = urllib2.OpenerDirector()
  for clazz in [
    urllib2.ProxyHandler,
    urllib2.UnknownHandler,
    urllib2.HTTPHandler,
    urllib2.HTTPDefaultErrorHandler,
    urllib2.HTTPRedirectHandler,
    urllib2.FTPHandler,
    urllib2.HTTPErrorProcessor,
    urllib2.HTTPSHandler
  ]: opener.add_handler(clazz())

  # Issue new http requests due to meta-refresh redirect at most 3 times.
  refresh_count = 3
  while refresh_count:
    refresh_count -= 1
    request = urllib2.Request(url=url, data=data)
    if user_agent is not None:
      request.add_header('User-Agent', user_agent)
    for header in request_headers:
      if header:
        keyval = re.split(r':\s*', header, 1)
        if len(keyval) != 2:
          output({'error': {'HeaderError': 'Malformed header %s' % header}})
          sys.exit(0)
        request.add_header(*keyval);
    response = opener.open(request)
    url = response.url
    content = response.read()
    headers = response.info()
    if requested_encoding is None:
      encoding = headers.getparam('charset')
    else:
      encoding = requested_encoding
    decoded = None
    parseargs = { 'fromEncoding': encoding }
    if extract == 'text' or extract == '*':
      parseargs['convertEntities'] = 'html'
    soup = BeautifulSoup(content, **parseargs)
    refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
    if refresh:
      refresh_url = re.sub(r'.*url=([^;]+)($|;)', r'\1', refresh['content'])
      if refresh_url:
        refresh_url = urlparse.urljoin(url, refresh_url)
        if refresh_url != url:
          url = refresh_url
          continue
    encoding = soup.originalEncoding
    if select:
      decoded = soupselect.select(soup, select)
      if extract == 'dict':
        decoded = [dictify(t) for t in decoded]
      elif extract == 'text':
        decoded = [u''.join(striptag(t)) for t in decoded]
      elif extract is not None and extract.startswith('attr_'):
        attr = extract[5:]
        decoded = [t.get(attr, None) for t in decoded]
      else:
        decoded = [d is not None and unicode(d) or None for d in decoded]
    elif extract == 'text':
      decoded = u''.join(stripinvisible(soup))
    else:
      codec = codecs.lookup(encoding)
      decoded = codec.decode(content)[0]

  # package the response
  output(OrderedDict((
          ('url', url),
          ('headers', OrderedDict([(k, headers[k]) for k in headers.keys()])),
          ('original-encoding', encoding),
          ('content', decoded))))

except urllib2.URLError, e:
  output({'error': {'URLError': str(e)}})
  sys.exit(0)
except urllib2.HTTPError, e:
  output({'error': {'HTTPError': e.code}})
  sys.exit(0)
except Exception, e:
  output({'error': {'Exception': str(e)}})
  sys.exit(0)

