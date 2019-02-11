## Lazo

[![PyPI version](https://badge.fury.io/py/lazo.svg)](https://badge.fury.io/py/lazo)

Small utility to upgrade Rancher images. It has been developd to be used in CI environments.

### Install


    $ pip install lazo
    
or using [pipsi](https://pypi.org/project/pipsi/) 

    $ pipsi install lazo
    
### Help        
        
    $ lazo --help
    Usage: lazo [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --version        Show the version and exit.
      --env
      -v, --verbosity  verbosity level
      -q, --quit       no output
      -d, --dry-run    dry-run mode
      --debug          debug mode
      -h, --help       Show this message and exit.
    
    Commands:
      docker
      rancher    


### Environment varialbles      

- RANCHER_BASE_URL as `--base-url`
- RANCHER_KEY as `--key`
- RANCHER_SECRET as `--secret`
- RANCHER_CLUSTER as `--cluster`
- RANCHER_PROJECT as `--project`
- RANCHER_INSECURE as `--inxecure`
- DOCKER_REPOSITORY as `--repository`

You can inspect your default configuration with:

    $ lazo --env
    Env                  Value                          Default                        Env value
    DOCKER_REPOSITORY    https://hub.docker.com/v2      https://hub.docker.com/v2
    RANCHER_AUTH         <SET>                                                         <SET>
    RANCHER_BASE_URL     https://r.example.com/v3                                      https://r.example.com/v3
    RANCHER_CLUSTER      cluster1                                                      cluster1
    RANCHER_INSECURE     False                          False
    RANCHER_PROJECT      bitcaster                                                     bitcaster
    RANCHER_USE_NAMES    False                          False
    RANCHER_WORKLOAD          
      
### Examples

    $ lazo upgrade cluster1:worload1 saxix/devpi:latest \
           --key api-key \
           --secret api-secret \
           --base-url https://rancher.example.com/v3/
           --cluster c-wwk6v
           --project p-xd4dg
               
Use environment variables

    $ export RANCHER_KEY=key
    $ export RANCHER_SECRET=secret
    $ export RANCHER_CLUSTER=c-wwk6v
    $ export RANCHER_PROJECT=p-xd4dg
    $ export RANCHER_ENDPOINT=https://rancher.example.com/v3/
    $
    $ lazo upgrade namespace:worload1 saxix/devpi:latest \

Use stdin to read credentials

    $  cat .pass.txt | lazo --stdin \
                            upgrade bitcaster:bitcaster \
                            bitcaster/bitcaster:0.3.0a10 \
                            --insecure

Examples:
--------
   
    $ lazo rancher -i -n info -p cluster1:bitcaster -w bitcaster:bitcaster
    Workload infos:
        Image: bitcaster/bitcaster:0.3.0a15
        Command: ['stack']
        imagePullPolicy: Always    

    $ lazo docker info saxix/devpi
    latest
    2.3
    2.2
    2.1
    2.0
    1.1


    $ lazo docker info library/python --filter '3\.6.*alpine3.8' --size
    3.6-alpine3.8                  26.2MiB
    3.6.8-alpine3.8                26.2MiB
    3.6.7-alpine3.8                26.2MiB
    3.6.6-alpine3.8                26.2MiB
