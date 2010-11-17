#!/usr/bin/env python

"""
Generate lod.js Protovis data file.
"""

import os
import sys
import json
import time
import urllib
import logging
import traceback

from datetime import datetime


LOG_FILE = "ckan.log"
LOG_LEVEL = logging.INFO


def main(argv):
    """talk to ckan rest api and generate lod.js
    """
    configure_logging()
    log = logging.getLogger()
    log.info("starting to load data from ckan")

    try:
        packages = lod_packages()
        javascript = protovis_javascript(packages)
        write_javascript(javascript)
    except BaseException, e:
        traceback.print_exc()
        log.fatal("exiting after unexpected error: %s" % e)

    log.info("finished ckan load")


def lod_packages():
    """returns a list of package metadata from ckan
    """
    log = logging.getLogger()
    packages = []
    count = 0
    for package in ckan('group/lodcloud')['packages']:
        package_info = ckan('package/%s' % package)
        if package_info == None:
            log.error("unable to retrieve package info for %s" % package)
            continue
        package_info['internal_id'] = count
        packages.append(package_info)
        log.info("got info for %s" % package_info['name'])
        count += 1
    return packages


def ckan(path):
    """gets a JSON resource via the CKAN API
    """
    log = logging.getLogger()
    u = 'http://ckan.net/api/rest/' + path
    r = urllib.urlopen('http://ckan.net/api/rest/' + path)
    if r.getcode() == 200:
        return json.loads(r.read())
    else:
        log.error("%s from ckan, unable to retrieve %s" % (r.getcode(), u))
        return None


def protovis_javascript(packages):
    """generates protovis javascript data file
    """
    protovis = {'nodes': get_nodes(packages), 
                'links': get_links(packages)}
    javascript = "var lod = " + json.dumps(protovis, indent=2)
    return javascript


def write_javascript(javascript):
    """safely writes protovis javascript to lod.js as well as 
    last_update.html that records the last time lod.js was updated.
    """
    now = datetime.now()
    tmp_file = "lod.js-%s" % datetime.strftime(now, "%Y%m%dT%H%M%S")

    open(tmp_file, "w").write(javascript)
    os.rename(tmp_file, "lod.js")

    tz = time.tzname[1] if time.daylight else time.tzname[0]
    t = datetime.strftime(now, "%Y-%m-%d %H:%M:%S ") + tz 
    file("last_update.html", "w").write("<span>last update: %s</span>" % t)


def get_nodes(packages):
    """constructs a list of nodes suitable for protovis
    """
    nodes = []
    for package in packages:
        if package['ratings_average'] == None:
            rating = None
        else:
            rating = float(package['ratings_average'])
        if 'triples' in package['extras']:
            triples = int(package['extras']['triples'])
        else:
            triples = 1000
        if 'shortname' in package['extras']:
            short_title = package['extras']['shortname']
        else:
            short_title = package['title']
        nodes.append({
            'ratings_average': rating,
            'ratings_count': package['ratings_count'],
            'nodeName': short_title,
            'nodeTitle': package['title'],
            'ckanUrl': 'http://ckan.net/package/%s' % package['name'],
            'triples': triples})
    return nodes


def get_links(packages):
    """returns links between the nodes suitable for protovis
    """
    log = logging.getLogger()

    # first get a dictionary lookup for all the packages by name
    package_map = {}
    for package in packages:
        package_map[package['name']] = package

    # now generate links based on the numeric id of the package
    links = []
    for from_package in packages:
        for key in from_package['extras']:
            if key.startswith('links:'):
                to_package_name = key.split(':')[1]
                if not package_map.has_key(to_package_name):
                    log.error("%s has link to %s which doesn't exist" % \
                            (from_package['name'], to_package_name))
                    continue
                try:
                    count = int(from_package['extras'][key])
                except ValueError:
                    count = 1
                links.append({
                    'source': from_package['internal_id'],
                    'target': package_map[to_package_name]['internal_id'],
                    'count': count})
    return links


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("""[%(asctime)s %(levelname)s %(name)s] %(message)s""")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    main(sys.argv)
