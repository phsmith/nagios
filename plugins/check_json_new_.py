#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author:  Phillipe Smith <phillipelnx@gmail.com>
# Date:    08/07/2014
# License: GPL
# Version: 1.2
#
# The checks verifies a JSON url result and generates a Nagios compatible service with the results
#
# Check options:
#     -h  Help message
#     -u  URL with JSON rsult
#     -f  Regular expression for filter only determined results
#     -p  Generates perfdata. Need
#
# Example of output gerenerated:
#     $./check_json.py -u http://date.jsontest.com/
#      JSON Status API OK - date: 07-12-2014, milliseconds_since_epoch: 1405126483908, time: 12:54:43 AM
#
# TODO:
#     Add Warning and Critical configuration
#

import json
import sys
import re
from optparse import OptionParser
from urllib2 import urlopen, Request, URLError, HTTPError

parser = OptionParser(usage='usage: %prog [ -u|--url http://json_result_url ] [ -f|--filter filter_expression ] [ -p|--perfdata ]')
parser.add_option('-u', '--url', dest='url', help='JSON api url')
parser.add_option('-f', '--filter', dest='filter', default='', help='Filter determined values. Ex.: "^tcp|^udp"')
parser.add_option('-p', '--perfdata', dest='perfdata', default=False, help='Enable performance data. Must specify a expression with the values that going to be used as perfdata. If you want to show all values as perfdata put a "."')
parser.add_option('-s', '--sort', dest='sort', action='store_true', help='Order output message alphabetically')
parser.add_option('-t', '--thresholds', dest='thresholds', default='', help='Define warning and critical values for specified fields')

(option, args) = parser.parse_args()

# Nagios status and messages
nagios_status = ['OK', 'WARNING', 'CRITICAL', 'UNKNOW']

filter     = option.filter
perfdata   = option.perfdata
sort       = option.sort
thresholds = option.thresholds

def exit(status, message):
    print 'JSON Status API %s - %s' % (nagios_status[int(status)], message)
    sys.exit(status)

def walk(data, levels = [], result = []):
    if isinstance(data, list):
        for item in data:
            walk(item)
    elif isinstance(data, dict):
        for key, value in data.iteritems():
            if isinstance(value, dict):
                levels.append(key)
                walk(value)
                levels.pop()
            else:
                prekeys = '.'.join(levels) + '.' if levels else ''
                info    = '%s%s: %s' % (prekeys, key, value)
                if re.search(filter, info):
                    result.append(info)
    return result

def pprint(data, ident = 0):
    if isinstance(data, list):
        print
        for item in data:
            pprint(item, ident + 1)
    elif isinstance(data, dict):
        print
        for key, value in data.items():
            print '  ' * ident, key + ':',
            pprint(value, ident + 1)
    else:
        print data

def output(data):
    perf     = []
    textinfo = walk(data)
    status   = 0

    if perfdata:
        for value in textinfo:
            if re.search(perfdata, value, re.IGNORECASE):
                perf.append(value.replace(': ', '=') + ';;')

    if thresholds:
        thrperf  = []
        txtinfo  = []
        for value in thresholds.split(','):
            thrkey, warning, critical = value.split(':')

            if perf:
                for item in perf:
                    perfsplit = item.split('=')
                    perfkey = perfsplit[0]
                    perfval = perfsplit[1].replace(';;', '')
                    
                    if thrkey in item:
                        perf.remove(item)
                        thrperf.append('%s=%s;%s;%s;' % (perfkey, perfval, warning, critical))

            for info in textinfo:
                infokey, infoval = info.split(': ')
                
                if critical >= infoval:
                    status = 2
                    textinfo.remove(info)
                    txtinfo.append('%s (crit at %s)' % (info, critical))
                elif warning >= infoval:
                    status = 1
                    textinfo.remove(info)
                    txtinfo.append('%s (warn at %s)' % (info, warning))
        textinfo += txtinfo
        perf += thrperf


    if not textinfo:
        exit(3, 'No value information with the filter specified.')

    if sort:
        message = ', '.join(sorted(textinfo))
        perf    = ' '.join(sorted(perf))
    else:
        message = ', '.join(textinfo)
        perf    = ' '.join(perf)

    return exit(status, message + ' | ' + perf) if perf else exit(0, message)

if not option.url:
    exit(3, 'Missing command line arguments')

try:
    request  = Request(option.url)
    response = urlopen(request)
except URLError as err:
    exit(3, 'Url request error. %s' % err)
except HTTPError as err:
    exit(3, 'Invalid Uri. %s' % err.reason)
else:
    try:
        json_response = json.loads(response.read().decode('iso-8859-1'))
    except Exception, e:
        exit(3, 'Invalid JSON response. %s' % e)

#pprint(json_response)
print output(json_response)

