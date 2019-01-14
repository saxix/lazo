## Lazo

[![PyPI version](https://badge.fury.io/py/lazo.svg)](https://badge.fury.io/py/lazo)

Small utility to upgrade Rancher images. It has been developd to be used in CI environments.

### Install


    $ pip install lazo
    
or using [pipsi](https://pypi.org/project/pipsi/) 

    $ pipsi install lazo
    
### Help        
        
    Usage: lazo [OPTIONS] COMMAND [ARGS]...
    
      lazo aims to help deployment on new version of Rancher workloads.
    
    Options:
      --version                       Show the version and exit.
      -v, --verbosity                 verbosity level
      -q, --quit                      no output
      -k, --key KEY                   Rancher API Key (username)
      -s, --secret SECRET             Rancher API secret (password)
      --stdin                         Read credentials from stdin
      -r, --repository URL            Docker repository
      --check-image / --no-check-image
                                      Do not check Docker repository
      -b, --base-url URL              Rancher base url
      -c, --cluster TEXT              Rancher cluster key
      -p, --project TEXT              Rancher project key  [required]
      -i, --insecure                  Ignore verifying the SSL certificate
      -d, --dry-run                   dry-run mode
      --pull [IfNotPresent|Always|Never]
                                      Rancher ImagePullPolicy
      --name TEXT                     Workload new name
      -h, --help                      Show this message and exit.
    
    Commands:
      upgrade      
      
      
### Environment varialbles      

- RANCHER_ENDPOINT as `--base-url`
- RANCHER_KEY as `--key`
- RANCHER_SECRET as `--secret`
- RANCHER_CLUSTER as `--cluster`
- RANCHER_PROJECT as `--project`

      
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
