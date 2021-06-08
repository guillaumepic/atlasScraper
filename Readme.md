# opsManBottle
# Purpose command to pull measurement from Ops Manager
# Measurements will be scraped for Prometheus
# GPI October 2019


## Dependencies

PyYAML	5.1.2	5.1.2
bottle	0.12.17	0.12.17
certifi	2019.9.11	2019.9.11
chardet	3.0.4	3.0.4
idna	2.8	2.8
requests	2.22.0	2.22.0
setuptools	40.8.0	41.4.0
urllib3	1.25.6	1.25.6


## Usages

>>  python f_opsmanBottle.py --url "https://ec2-3-9-206-23.eu-west-2.compute.amazonaws.com:8443" --username opsmgr@example.com --key 78f1291f-1d9f-44a8-b8aa-77ccb69074a1 --cfg f_opsmanBottle.yml 
WARNING: Executing a script that is loading libcrypto in an unsafe way. This will fail in a future version of macOS. Set the LIBRESSL_REDIRECT_STUB_ABORT=1 in the environment to force this into an error.
f_opsmanBottle.py :: Configuration file found f_opsmanBottle.yml
f_opsmanBottle.py :: Mapping Project: GPIProj and Cluster: shGPI_0
f_opsmanBottle.py :: cluster is found. Bottle is proceeding ... 
f_opsmanBottle.py :: Ops Manager Proxy starts listening on 0.0.0.0:8080
Bottle v0.12.13 server starting up (using WSGIRefServer())...
Listening on http://0.0.0.0:8080/
Hit Ctrl-C to quit.
...


Typical API ressource request generated
>> curl -k --user "opsmgr@example.com:78f1291f-1d9f-44a8-b8aa-77ccb69074a1" --digest  --header "Accept: application/json"  --include --request GET https://ec2-3-9-206-23.eu-west-2.compute.amazonaws.com:8443/api/public/v1.0/groups/5d5bde680c5cd368e9cb29a3/hosts/?pretty=true&clusterId=5d5be5a40c5cd368e9cb3543


>> curl http://localhost:8080/alive
{"errorCode":"NONE","version":"1","status":"OK"}


## Version notes :
1.0 octobre 2019
 - replica Set only
 - hostname not in the metric label

1.3 octobre 2019:
 - shard compatible
 - hostname in the metrics label
 - few coding enhancement


