#!/usr/bin/env python
#
# Brief :
# https://docs.atlas.mongodb.com/reference/api/access-tracking-get-database-history-clustername/
# Usage : See --help
#
# GPI June 2021

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Union

from timeloop import Timeloop

import requests
import yaml
from bottle import route, run, response, abort, request
from requests.auth import HTTPDigestAuth

__author__ = 'gpi'

# CONSTANTS & globals
LOG = __file__ + " :: "
g_atlasUrl = "https://cloud.mongodb.com/api/atlas/v1.0"
g_sslMode = True
__version__ = "1.0"
g_periodicThread = Timeloop()


def f_print(log, verbose=False):
    if verbose:
        print(__file__ + " :: " + log)


@g_periodicThread.job(interval=timedelta(seconds=3600))
def discoveryTask():
    f_print("Periodic job current time : {}".format(str(datetime.utcnow())), g_verbose)
    g_clusters = get_clusters()
    f_print("Cluster list update: [{0}]".format(', '.join(map(str, g_clusters["results"]))), g_verbose)


@route('/ready')
def ready():
    """Brief: Testing Ready to Bottle rest API"""

    # Basically healtcheck
    try:
        global_r = requests.get(g_atlasUrl,
                                auth=HTTPDigestAuth(str(args.publicKey),
                                                    str(args.privateKey)),
                                verify=g_sslMode)
        global_r.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        print(LOG + " Http Error:", errh)
        return abort(500, "Sorry, Atlas could not be accessed.")
    except requests.exceptions.ConnectionError as errc:
        print(LOG + " Error Connecting:", errc)
        return abort(500, "Sorry, Atlas could not be accessed.")
    except requests.exceptions.Timeout as errt:
        print(LOG + " Timeout Error:", errt)
        return abort(500, "Sorry, Atlas could not be accessed.")
    except requests.exceptions.RequestException as err:
        print(LOG + " Bad request", err)
        return abort(500, "Sorry, Atlas could not be accessed.")

    res = dict()
    if global_r:
        f_print("Called /ready is ok", g_verbose)
        res['happy'] = 'yes'
        res['statusCode'] = global_r.status_code
    else:
        f_print("something not ok in calling /ready", g_verbose)
        res['happy'] = 'no'
        res['statusCode'] = global_r.status_code
    response.headers['Content-Type'] = 'application/json'
    return res


def f_dbAccessHistory(cName):
    """Brief: Get dbAccess History"""

    try:
        if not g_proxySettings["start"]:
            accesses_r = requests.get("{0}/dbAccessHistory/clusters/{1}/?authResult=false".format(g_baseUrl,
                                                                                                  str(cName)),
                                      auth=HTTPDigestAuth(str(args.publicKey),
                                                          str(args.privateKey)),
                                      verify=g_sslMode)
        else:

            if g_proxySettings["deltaUnit"] == "seconds":
                delta = timedelta(seconds=g_proxySettings["deltaValue"])
            elif g_proxySettings["deltaUnit"] == "minutes":
                delta = timedelta(minutes=g_proxySettings["deltaValue"])

            p_start = (datetime.utcnow() - delta).replace(tzinfo=timezone.utc)
            f_print("Scraping dbAccessHistory with start parameter {}".format(str(p_start)))
            accesses_r = requests.get("{0}/dbAccessHistory/clusters/{1}/?authResult=false&start={2}".format(g_baseUrl,
                                                                                                            str(cName),
                                                                                                            str(p_start.timestamp()*1000).rsplit('.')[0]),
                                      auth=HTTPDigestAuth(str(args.publicKey),
                                                          str(args.privateKey)),
                                      verify=g_sslMode)
        accesses_r.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        print(LOG + "Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print(LOG + "Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print(LOG + "Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print(LOG + "Bad request", err)

    return accesses_r


@route('/accesses/<cluster>', method='GET')
def get_dbAccessHistory(cluster):
    """ Brief: GET Json response for accesses history"""

    accesses_r = f_dbAccessHistory(str(cluster))
    if accesses_r:
        accesses_j = accesses_r.json()
        alist = [p for p in accesses_j["accessLogs"] if (p["authResult"] == False)]
        if alist:
            f_print("Got accesses entries with authResult to False", g_verbose)
        else:
            f_print("Got no accesses entries with authResult to False", g_verbose)
        res = dict()
        res['count'] = len(alist)
        res['detectionDate'] = str(datetime.utcnow())
        res['statusCode'] = accesses_r.status_code
        res['detections'] = alist
        response.headers['Content-Type'] = 'application/json'
    return res


@route('/accesses/<cluster>/toProm', method='GET')
def get_dbAccessHistory2Prom(cluster):
    """ Brief: GET custom formatted response for Prometheus"""

    accesses_r = f_dbAccessHistory(cluster)
    if accesses_r:
        accesses_j = accesses_r.json()
        alist = [p["username"] for p in accesses_j["accessLogs"] if (p["authResult"] == False)]
        if alist:
            f_print("Got accesses entries with authResult to true", g_verbose)
            result = "atlas_metrics{{projectID=\"{1}\",cluster=\"{0}\"}}{2}".format(str(cluster),
                                                                                    str(g_proxySettings["PROJ"]),
                                                                                    str(len(alist)))
        else:
            f_print("Got no accesses entries with authResult to true", g_verbose)
            result = "atlas_metrics{{projectID=\"{1}\",cluster=\"{0}\"}}{2}".format(str(cluster),
                                                                                    str(g_proxySettings["PROJ"]),
                                                                                    str(0))
    return result


@route('/accesses/toProm', method='GET')
def get_dbAccessHistory2PromFull():
    """ Brief: GET custom formatted response for Prometheus"""

    result = ""
    for c in g_clusters["results"]:
        accesses_r = f_dbAccessHistory(c)
        if accesses_r:
            accesses_j = accesses_r.json()
            alist = [p["username"] for p in accesses_j["accessLogs"] if (p["authResult"] == False)]
            if alist:
                f_print("Got accesses entries with authResult to true", g_verbose)
                result_c = "atlas_metrics{{projectID=\"{1}\",cluster=\"{0}\"}}{2}".format(str(c),
                                                                                          str(g_proxySettings["PROJ"]),
                                                                                          str(len(alist)))
            else:
                f_print("Got no accesses entries with authResult to true", g_verbose)
                result_c = "atlas_metrics{{projectID=\"{1}\",cluster=\"{0}\"}}{2}".format(str(c),
                                                                                          str(g_proxySettings["PROJ"]),
                                                                                          str(0))
            result = result + "\n" + result_c
    return result


def get_clusters():
    """Brief: Detect clusters in project object informations from Atlas.
     When found, cluster names are validated """

    try:
        clusters_r = requests.get("{0}/clusters".format(g_baseUrl),
                                  auth=HTTPDigestAuth(str(args.publicKey),
                                                      str(args.privateKey)),
                                  verify=g_sslMode)
        clusters_r.raise_for_status()

    except requests.exceptions.HTTPError as errh:
        print(LOG + "Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print(LOG + "Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print(LOG + "Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print(LOG + "Bad request", err)

    if clusters_r:
        clusters_r = clusters_r.json()
        return {"ret": True, "results": [c["name"] for c in clusters_r["results"]]}
    else:
        return {"ret": False}


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="http Atlas proxy rest-end point")
    required = parser.add_argument_group("Required arguments")

    required.add_argument("--publicKey", help="Atlas public key",
                          required=True)
    required.add_argument("--privateKey", help="Atlas secret key", required=True)
    required.add_argument("--cfg", help="Configuration yaml file",
                          required=True,
                          default="f_atlasScraper.yml")
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("--verbose", help="Enable stdout printing of logs",
                          action="store_true")
    args = parser.parse_args()

    g_proxySettings: Dict[str, Union[Union[List[Any], bool], Any]] = {}
    g_clusters: Dict[str, Union[Union[List[Any], bool], Any]] = {}
    g_verbose = args.verbose

    if args.cfg:
        f_print("Configuration file found " + str(args.cfg), g_verbose)
        if os.path.exists(args.cfg) is False:
            f_print("WARNING yaml configuration file is not found : " + args.cfg, g_verbose)
        cfg = yaml.safe_load(open(str(args.cfg)))
        g_proxySettings["PROJ"] = cfg["topology"]["groupID"]
        g_proxySettings["start"] = cfg["scraper"]["start"]
        g_proxySettings["deltaUnit"] = cfg["scraper"]["deltaUnit"]
        g_proxySettings["deltaValue"] = cfg["scraper"]["deltaValue"]
        if g_proxySettings["deltaUnit"] not in ["minutes", "seconds"]:
            f_print("Sorry scraper configuration as incorrect delta units (seconds or minutes) !! ... ", g_verbose)
            sys.exit(1)
    else:
        f_print("Sorry no configuration file found !! ... ", g_verbose)
        sys.exit(1)

    # Base URL
    g_baseUrl = g_atlasUrl + "/groups/" + str(g_proxySettings["PROJ"])

    # Get project & clusters
    g_clusters = get_clusters()
    if g_clusters["ret"]:
        f_print("Mapping Project: " + g_proxySettings["PROJ"] +
                " and Clusters: [{0}]".format(', '.join(map(str, g_clusters["results"]))), g_verbose)
        f_print("clusters are found. Bottle is proceeding ... ", g_verbose)
        g_periodicThread.start(block=False)
        f_print("Atlas Proxy starts listening on " +
                str(cfg["net"]["bindIP"]) + ":" + str(cfg["net"]["port"]), g_verbose)
        run(host=cfg["net"]["bindIP"], port=cfg["net"]["port"], debug=True)
    else:
        f_print("ERROR no cluster found with matching name !! ... ", g_verbose)
        sys.exit(1)

    f_print("Bye ...", g_verbose)
    sys.exit(0)
