## AtlasAccessScraper
Creation Date : June 2021 

### Brief

* Purpose command to pull access events from Atlas.
* Events are filtered with authResult=False and counted
* Routes for targeted cluster names
* Routes for dynamical discovery of existing cluster in the same project
* Routes to format resulting counting into compliant format for Prometheus

### Atlas Reference doc
* https://docs.atlas.mongodb.com/reference/api/access-tracking/#access-tracking


### Dependencies
* bottle==0.12.19
* PyYAML==5.4.1
* requests==2.25.1
* timeloop==1.0.2
* urllib3==1.26.5

### Usages

Helper example :
```shell
$ python3 f_atlasScraper.py --publicKey <yourPublic> --privateKey <yourPrivate> --cfg f_atlasScraper_PS.yml --help

usage: f_atlasScraper.py [-h] --publicKey PUBLICKEY --privateKey PRIVATEKEY
                         --cfg CFG [--verbose]

http Atlas proxy rest-end point

optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  --publicKey PUBLICKEY Atlas publicKey
  --privateKey PRIVATEKEY Atlas privateKey
  --cfg CFG             Configuration yaml file

Optional arguments:
  --verbose             Enable stdout printing of logs
```

Requires yaml configuration file :
````yaml
net:
  port: 8080
  bindIP: 0.0.0.0

topology:
  groupID: "<yourAtlasProjectId>"

scraper:
  start: true
  deltaUnit : seconds
  deltaValue : 900
````
### Routes

* Basic healthcheck

```shell
$ curl --request GET http://localhost:8080/ready
{
    "happy": "yes",
    "statusCode": 200
}
```

* authResult False accesses for targeted clustername
```shell
$ curl --request GET http://localhost:8080/accesses/<clusterName>
{
    "count": 6,
    "detectionDate": "2021-06-08 15:56:32.588876",
    "statusCode": 200,
    "detections": [
        {
            "authResult": false,
            "authSource": "admin",
            "failureReason": "UserNotFound: Could not find user \"TARZAN\" for db \"admin\"",
            "groupId": "xxxx",
            "hostname": "xxxx",
            "ipAddress": "xxxxx",
            "logLine": "xxxxx",
            "timestamp": "Tue Jun 08 15:49:25 GMT 2021",
            "username": "TARZAN"
        }],
        ...
}
```
* Custom formatted count for targeted clustername
````shell
$ curl --request GET http://localhost:8080/accesses/<clusterName>/toProm
atlas_metrics{projectID="xxxxx",cluster="xxxx"}6
````

* Custom formatted count for discovered clusternames
````shell
$ curl --request GET http://localhost:8080/accesses//toProm
atlas_metrics{projectID="xxxxx",cluster="xxxx"}6
atlas_metrics{projectID="xxxxx",cluster="yyyyy"}10
````

### Prometheus configuration
Sample job definition
````yaml
  - job_name: 'atlas_metrics'
    scrape_interval: 15s
    metrics_path: /accesses/toProm
    static_configs:
    - targets: ['localhost:8080']
      labels:
        group: 'atlas_metrics'
````

#### Release notes :
1.0  June 2021
- Start parameter accept minutes or seconds only. Consolidation required
- Project identifier should be expose in the routes instead of configured




