#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# Author:  Phillipe Smith <phillipelnx@gmail.com>
# Date:    08/07/2014
# License: GPL
# Version: 1.3
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
#     OK - date: 09-13-2018, milliseconds_since_epoch: 1536860376248, time: 05:39:36 PM | date=09-13-2018; milliseconds_since_epoch=1536860376248; time=05:39:36 PM;
#

import json
import sys
import re
import requests
from argparse import ArgumentParser

#parser = ArgumentParser(usage='usage: %prog [ -u|--url http://json_result_url ] [ -f|--filter filter_expression ] [ -p|--perfdata ]')
parser = ArgumentParser()
parser.add_argument('-u', '--url', dest='url', help='JSON api url')
parser.add_argument('-f', '--filter', dest='filter', default='', help='Filter determined values. Ex.: "^tcp|^udp"')
parser.add_argument('-e', '--exclude', dest='exclude', help='Exclude a part of the metrics name. Ex.: "(counter|gauge)."')
parser.add_argument('-s', '--sort', dest='sort', action='store_true', help='Order output message alphabetically')
parser.add_argument('-t', '--threshold', dest='threshold', default='', help='Add thresholds for waning and critical. Ex.: counter:100:200')
parser.add_argument('-p', '--perfdata', dest='perfdata', default='.', help='Filter perfdata to show only values matched by a regex')
parser.add_argument('--no-perfdata', dest='no_perfdata', action='store_true', help='Disable perfdata')

args = parser.parse_args()

# Nagios status and messages
nagios_status = ['OK', 'WARNING', 'CRITICAL', 'UNKNOW']

def exit(status, message):
    print '%s - %s' % (nagios_status[int(status)], message.encode('iso-8859-1'))
    sys.exit(status)

def walk(data, levels = [], result = []):
    if isinstance(data, list):
        for item in data:
            walk(item)
    elif isinstance(data, dict):
        for key, value in data.iteritems():
            if isinstance(value, dict) or isinstance(value, list):
                levels.append(key)
                walk(value)
                levels.pop()
            else:
                prekeys = '.'.join(levels) + '.' if levels else ''
                info    = '%s%s: %s' % (prekeys, key, value)
                if args.threshold:
                    for threshold in args.threshold.split(','):
                        threshold = threshold.split(':')
                        if threshold[0] in key:
                            if threshold[2] and value > float(threshold[2]):
                                info  += '(!!);%s;%s;' % (threshold[1], threshold[2])
                            elif threshold[1] and value > float(threshold[1]):
                                info  += '(!);%s;%s;' % (threshold[1], threshold[2])

                if re.search(args.filter, info):
                    result.append(info)
    return result

def output(data):
    status   = 0
    perf     = []
    textinfo = walk(data)

    for value in textinfo:
        if re.match(args.perfdata, value, re.IGNORECASE):
            value = re.sub('\(!!?\)', '', value.replace(': ', '='))
            perf.append(value+';')

    if args.exclude:
        textinfo = map(lambda x: re.sub('('+args.exclude+'|;.*)','',x), textinfo)
        perf     = map(lambda x: re.sub(args.exclude,'',x), perf)

    if not textinfo:
        exit(3, 'No value information with the filter specified.')

    if args.sort:
        message = ', '.join(sorted(textinfo))
        perf    = ' '.join(sorted(perf))
    else:
        message = ', '.join(textinfo)
        perf    = ' '.join(perf)

    if '(!!)' in message:
        status = 2
    elif '(!)' in message:
        status = 1

    if args.no_perfdata == False:
        return exit(status, message + ' | ' + perf)
    else:
        return exit(status, message)

if not args.url:
    exit(3, 'Missing command line arguments')

try:
    requests.packages.urllib3.disable_warnings()
    response = requests.get(args.url, verify=False)
except Exception, err:
    exit(3, 'Error: %s' % err)
else:
    try:
        json_response = response.json()
    except Exception, e:
        exit(3, 'Invalid JSON response. %s' % e)

print output(json_response)

