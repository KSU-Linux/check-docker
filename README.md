# Check Docker

Python script to check various aspects of Docker and Docker Swarm. It can verify that the daemon is up, is a part of a Swarm, and if Swarm services are healthy.

The `check-docker.py` script is a re-implentation of [check_docker](https://github.com/timdaman/check_docker) using the native Docker Python SDK and combines it into a single command.

# Sensu Go Asset

To use as an asset, clone this repository and create a tarball using `make`.

```bash
git clone https://github.com/KSU-Linux/check-docker.git
cd check-docker
make all
```

This will generate the files `check-docker.tar.gz` and `sha512sum.txt`. You will need to upload `check-docker.tar.gz` to a downloadable URL which you can then reference in a Sensu Go asset definition.

```yaml
---
type: Asset
api_version: core/v2
metadata:
  name: check-docker
spec:
  builds:
    - url: https://example.com/check-docker.tar.gz
      sha512: ${SHA512SUM}
      filters:
        - entity.system.os == 'linux'
        - entity.system.arch == 'amd64'
    - url: https://example.com/check-docker.tar.gz
      sha512: ${SHA512SUM}
      filters:
        - entity.system.os == 'linux'
        - entity.system.arch == '386'
```

# Docker Permissions for Sensu Go

In order for Sensu Go to run `docker` commands, add the user to the `docker` group on systems that will use the check.

```bash
gpasswd -a sensu docker
```

# Usage Examples

## Ping

This check will verify that the Docker daemon is up and repsonsive.

```bash
./check-docker.py --ping
OK: docker is up
```

### Containers

This check will confirm that there is at least 1 container up and running.

```bash
./check-docker.py --containers
OK: 4 running containers
```

#### Minimum/Maximum Running Containers

You can modify the minimum and maximum running containers for the `--containers` check using `--min` and `--max` respectively.

```bash
./check-docker.py --containers --min 1 --max 4
OK: 4 running containers
```

## Swarm

This check will check the node is part of a Swarm.

```bash
./check-docker.py --swarm
OK: Docker Swarm enabled
```

### Manager

This check confirms that the node is a Swarm manager.

```bash
./check-docker.py --swarm-manager
OK: Node is a manager
```

### Services

This check can be used to verify that one or more Swarm services are healthy.

```bash
./check-docker.py --swarm-service jirafeau_app traefik_proxy
OK: Docker Swarm service 'jirafeau_app' replicas 2/2; OK: Docker Swarm service 'traefik_proxy' replicas 2/2
```

### All Services

This check verifies all services in the Swarm.

```bash
./check-docker.py --swarm-services
OK: Docker Swarm service 'jirafeau_app' replicas 2/2; OK: Docker Swarm service 'traefik_proxy' replicas 2/2
```
