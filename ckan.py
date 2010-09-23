#!/usr/bin/env python

"""
This is a little script that will pull down all the package information
for packages in the lodcloud group on CKAN, and write out JSON dataset
for ProtoVis.
"""

import sys
import json
import urllib
import logging


LOG_FILE = "ckan.log"
LOG_LEVEL = logging.INFO


def main(argv):
    logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
    packages = lod_packages()
    protovis = protovis_json(packages)
    print "var lod = " + json.dumps(protovis, indent=2)


def lod_packages():
    log = logging.getLogger()
    packages = []
    count = 0
    for package in ckan('group/lodcloud')['packages']:
        package_info = ckan('package/%s' % package)
        package_info['internal_id'] = count
        packages.append(package_info)
        log.info("got info for %s" % package_info['name'])
        count += 1
    return packages


def protovis_json(packages):
    protovis = {'nodes': get_nodes(packages), 
                'links': get_links(packages)}
    return protovis


def get_nodes(packages):
    nodes = []
    for package in packages:
        if package['ratings_average'] == None:
            rating = 0
        else:
            rating = int(round(float(package['ratings_average'])))
        if 'triples' in package['extras']:
            triples = int(package['extras']['triples'])
        else:
            triples = 1000
        nodes.append({
            'rating': rating,
            'nodeName': package['title'],
            'triples': triples})
    return nodes


def get_links(packages):
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


def ckan(path):
    j = urllib.urlopen('http://ckan.net/api/rest/' + path).read()
    return json.loads(j)


def configure_logging():
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("""[%(asctime)s %(levelname)s %(name)s] %(message)s""")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    main(sys.argv)
