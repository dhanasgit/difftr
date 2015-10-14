#!/usr/bin/env python

from hashlib import md5
from pprint import pprint
from subprocess import Popen, PIPE
import difflib
import json
import re
import sys
import textwrap
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
  print('Usage: difftr <ktr1> <ktr2>')
  exit(1)

def wrap(s):
  return '\\n'.join(textwrap.wrap(s, 20)).replace('"', '\\"')

def hsh(s):
  return md5(s.encode('utf8')).hexdigest()

def normalize(xml):
  xml = re.sub(r'<([xy]loc|width|height)>.*?</\1>', '', xml)
  xml = re.sub(r'\r\n|\r|\n', '\n', xml)
  xml = re.sub(r'>\s*<', '>\n<', xml)
  xml = xml.strip()
  xml = re.sub(
    r'&#x([a-fA-F0-9]+);',
    lambda m: chr(int(m.group(1), 16)),
    xml
  )
  return xml

# Read the files and extract hop and steps

ktrs = [None, None]

for i in range(len(ktrs)):
  ktr = ET.parse(sys.argv[i + 1]).getroot()
  hops = {
    (wrap(n.findtext('./from')), wrap(n.findtext('./to')))
    for n in ktr.findall('./order/hop')
  }
  steps = {
    wrap(n.findtext('./name')): n
    for n in ktr.findall('./step')
  }
  ktr.remove(ktr.find('./order'))
  for n in ktr.findall('./step'):
    ktr.remove(n)
  ktrs[i] = {'meta': ktr, 'hops': hops, 'steps': steps}
 
# Determine diffs between common steps

diffs = {name:
  list(filter(lambda x: not x.startswith('?'), difflib.ndiff(
    normalize(
      ET.tostring(ktrs[0]['steps'][name], encoding='unicode')
    ).split('\n') if name in ktrs[0]['steps'] else [],
    normalize(
      ET.tostring(ktrs[1]['steps'][name], encoding='unicode')
    ).split('\n') if name in ktrs[1]['steps'] else []
  )))
for name in set(ktrs[0]['steps']) | set(ktrs[1]['steps'])}

meta_diff = list(filter(lambda x: not x.startswith('?'), difflib.ndiff(
  normalize(
    ET.tostring(ktrs[0]['meta'], encoding='unicode')
  ).split('\n'),
  normalize(
    ET.tostring(ktrs[1]['meta'], encoding='unicode')
  ).split('\n')
)))

# Build the digraph in graphviz format

dot = []

dot.append('digraph G {')
dot.append('  node [fontname="sans" shape=box style=filled width=0.5 fillcolor=white]')

# Steps

for added in set(ktrs[1]['steps']) - set(ktrs[0]['steps']):
  dot.append(
    '  "%s" [id="%s" fillcolor="#5fd35f"]' % (added, hsh(added)))

for delled in set(ktrs[0]['steps']) - set(ktrs[1]['steps']):
  dot.append(
    '  "%s" [id="%s" fillcolor="#ff5555"]' % (delled, hsh(delled)))

for umod in set(ktrs[0]['steps']) & set(ktrs[1]['steps']):
  if any(
    s.startswith('+') or s.startswith('-')
    for s in diffs[umod]
  ):
    dot.append('  "%s" [id="%s" fillcolor=yellow]' % (umod, hsh(umod)))
  else:
    dot.append('  "%s" [id="%s" fillcolor=white]' % (umod, hsh(umod)))

# Hops

for added_hop in ktrs[1]['hops'] - ktrs[0]['hops']:
  dot.append('  "%s" -> "%s" [color=green]' % added_hop)

for del_hop in ktrs[0]['hops'] - ktrs[1]['hops']:
  dot.append('  "%s" -> "%s" [color=red]' % del_hop)

for unmod_hop in ktrs[0]['hops'] & ktrs[1]['hops']:
  dot.append('  "%s" -> "%s" [color=black]' % unmod_hop)

dot.append('}')

# SVG

dot_proc = Popen(['dot', '-Tsvg'], stdin=PIPE, stdout=PIPE)
svg, _ = dot_proc.communicate('\n'.join(dot).encode('utf8'))
svg = re.sub(r'\s*<[?]xml[\s\S]+?<svg', '<svg', svg.decode('utf8'))

# Javascript

script = '''

function buildDiff(title, lines) {
  var diffWin = open('', new Date() + '', 'height=400,width=400');
  diffWin.document.title = 'diff: ' + title;
  var preEl = diffWin.document.createElement('pre');
  preEl.style.padding = '1em';
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    var lType = line.charAt(0);
    var spanEl = diffWin.document.createElement('div');
    spanEl.style.color = lType == '+' ? 'green' : (
      lType == '-' ? 'red' : '#999'
    );
    spanEl.style.fontWeight = lType == ' ' ? 'normal' : 'bold';
    var spanText = diffWin.document.createTextNode(line.substr(2));
    spanEl.appendChild(spanText);
    preEl.appendChild(spanEl);
  }
  diffWin.document.body.appendChild(preEl);
}

function showDiff(hsh) {
  buildDiff(diffNames[hsh], diffs[hsh]);
}

document.getElementById('show-mdiff').addEventListener('click', function() {
  buildDiff('meta diff', metaDiff);
});

var diffs = %s;
var diffNames = %s;
var metaDiff = %s;
for (var hsh in diffs) {
  var el = document.getElementById(hsh);
  (function(hsh) {
    el.addEventListener('click', function(e) {
      showDiff(hsh);
    });
  })(hsh);
  el.style.cursor = 'pointer';
}
''' % (json.dumps({
  hsh(name): value for name, value in diffs.items()
}), {hsh(name): name for name in diffs}, meta_diff)

# HTML

html = '''<!doctype html>
<html><body>
<div style="margin: 1em">
  <button id="show-mdiff">Show Meta Diff%s</button></div>
<div style="text-align: center">
%s
</div></body><script>%s</script></html>''' % (
  ' (+)' if any(not l.startswith(' ') for l in meta_diff) else '',
  svg,
  script
)

print(html)
