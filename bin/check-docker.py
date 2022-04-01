#!/usr/bin/env python3

import os 
import sys
import argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib')))

import docker

DEFAULT_MIN = 1
DEFAULT_MAX = sys.maxsize
DEFAULT_SOCKET = 'unix:///var/run/docker.sock'
DEFAULT_TIMEOUT = 10
OK_RC = 0
WARNING_RC = 1
CRITICAL_RC = 2
UNKNOWN_RC = 3

rc = -1
ok_messages = []
warning_messages = []
critical_messages = []
unknown_messages = []

def get_docker_api_client(parsed_args):
    base_url = parsed_args.base_url
    timeout = parsed_args.timeout
    tls = parsed_args.tls
    try:
        client = docker.APIClient(base_url=base_url, timeout=timeout, tls=tls)
        return client
    except Exception as e:
        unknown(str(e))
        return None

def get_docker_client(parsed_args):
    base_url = parsed_args.base_url
    timeout = parsed_args.timeout
    tls = parsed_args.tls
    try:
        client = docker.DockerClient(base_url=base_url, timeout=timeout, tls=tls)
        return client
    except Exception as e:
        unknown(str(e))
        return None

def set_rc(new_rc):
    global rc
    rc = new_rc if new_rc > rc else rc

def ok(message):
    set_rc(OK_RC)
    ok_messages.append('OK: ' + message)

def warning(message):
    set_rc(WARNING_RC)
    warning_messages.append('WARNING: ' + message)

def critical(message):
    set_rc(CRITICAL_RC)
    critical_messages.append('CRITICAL: ' + message)

def unknown(message):
    set_rc(UNKNOWN_RC)
    unknown_messages.append('UNKNOWN: ' + message)

def check_containers(api_client, minimum, maximum):
    try:
        info = api_client.info()
        running_containers = info['ContainersRunning']
        if minimum <= running_containers <= maximum:
            ok("{} running containers".format(running_containers))
        elif running_containers < minimum:
            critical("{} running containers".format(running_containers))
        elif running_containers > maximum:
            warning("{} running containers".format(running_containers))
    except docker.errors.APIError as e:
        unknown(str(e))
    except Exception as e:
        unknown(str(e))

def check_ping(api_client):
    try:
        if api_client.ping():
            ok("docker is up")
        else:
            critical("docker is down")
    except docker.errors.APIError as e:
        unknown(str(e))
    except Exception as e:
        unknown(str(e))

def check_swarm(api_client):
    try:
        info = api_client.info()
        swarm = info['Swarm']
        if swarm['LocalNodeState'] == 'active':
            ok('Docker Swarm enabled')
        else:
            critical('Docker Swarm not enabled')
    except docker.errors.APIError as e:
        unknown(str(e))
    except:
        unknown("An unknown error ocurred")

def check_swarm_manager(api_client):
    try:
        info = api_client.info()
        swarm = info['Swarm']
        if swarm['LocalNodeState'] == 'active':
            if swarm['ControlAvailable']:
                ok('Node is a manager')
            else:
                critical('Node is not a manager')
        else:
            critical('Docker Swarm not enabled')
    except docker.errors.APIError as e:
        unknown(str(e))
    except:
        unknown("An unknown error ocurred")

def check_swarm_service(docker_client, service_name):
    try:
        service = docker_client.services.get(service_name)
        service_mode = service.attrs['Spec']['Mode']
        if 'Global' in service_mode:
            mode = 'global'
            replicas = len(docker_client.nodes.list())
        elif 'Replicated' in service_mode:
            mode = 'replicated'
            replicas = service_mode['Replicated']['Replicas']
        else:
            mode = 'unknown'
            replicas = 0
        tasks = service.tasks()
        running_tasks = 0
        for task in tasks:
            if task['Status']['State'] == 'running':
                running_tasks += 1
        if running_tasks == 0:
            critical("Docker Swarm service '{}' replicas {}/{}".format(service_name, running_tasks, replicas))
        elif running_tasks < replicas:
            warning("Docker Swarm service '{}' replicas {}/{}".format(service_name, running_tasks, replicas))
        else:
            ok("Docker Swarm service '{}' replicas {}/{}".format(service_name, running_tasks, replicas))
    except docker.errors.NotFound as e:
        critical("Docker Swarm service '{}' not found".format(service_name))
    except docker.errors.APIError as e:
        unknown(str(e))
    except docker.errors.InvalidVersion as e:
        unknown(str(e))
    except:
        unknown("An unknown error ocurred")

def check_swarm_services(docker_client):
    try:
        services = docker_client.services.list()
        for service in services:
            check_swarm_service(docker_client, service.name)
    except docker.errors.APIError as e:
        unknown(str(e))
    except:
        unknown("An unknown error ocurred")

def print_results():
    if rc == OK_RC:
        print('; '.join(ok_messages))
    elif rc == WARNING_RC:
        print('; '.join(warning_messages))
    elif rc == CRITICAL_RC:
        print('; '.join(critical_messages))
    elif rc == UNKNOWN_RC:
        print('; '.join(unknown_messages))

def parse_args(unparsed_args):
    parser = argparse.ArgumentParser(description='check docker swarm')

    parser.add_argument('--base-url',
                        dest='base_url',
                        action='store',
                        default=DEFAULT_SOCKET,
                        type=str,
                        metavar='[unix:///path/to/docker.sock|tcp://1.2.3.4:2376]',
                        help='base url to connect to docker daemon (default: %(default)s)')

    parser.add_argument('--max',
                        dest='max',
                        action='store',
                        default=DEFAULT_MAX,
                        type=int,
                        help='maximum number of running containers for --containers check (default: none)')

    parser.add_argument('--min',
                        dest='min',
                        action='store',
                        default=DEFAULT_MIN,
                        type=int,
                        help='minimum number of running containers for --containers check (default: %(default)s)')

    parser.add_argument('--timeout',
                        dest='timeout',
                        action='store',
                        default=DEFAULT_TIMEOUT,
                        type=int,
                        help='timeout for api calls in seconds (default: %(default)s)')

    parser.add_argument('--tls',
                        dest='tls',
                        action='store_true',
                        default=False,
                        help='enable tls for base url')

    mutually_exclusive_group = parser.add_mutually_exclusive_group(required=True)

    mutually_exclusive_group.add_argument('--containers',
                        dest='containers',
                        action='store_true',
                        default=False,
                        help='check number of running containers')

    mutually_exclusive_group.add_argument('--ping',
                        dest='ping',
                        action='store_true',
                        default=False,
                        help='check that docker daemon is responsive')

    mutually_exclusive_group.add_argument('--swarm',
                             dest='swarm',
                             default=False,
                             action='store_true',
                             help='check swarm status')

    mutually_exclusive_group.add_argument('--swarm-manager',
                             dest='swarm_manager',
                             default=False,
                             action='store_true',
                             help='check node is swarm manager')

    mutually_exclusive_group.add_argument('--swarm-service',
                             dest='swarm_service',
                             action='store',
                             type=str,
                             nargs='+',
                             default=[],
                             help='one or more swarm services to check')

    mutually_exclusive_group.add_argument('--swarm-services',
                             dest='swarm_services',
                             action='store_true',
                             default=False,
                             help='check all swarm services')

    if len(unparsed_args) == 0:
        parser.print_help()

    parsed_args = parser.parse_args(args=unparsed_args)
    return parsed_args

def perform_checks(cli_args):
    args = parse_args(cli_args)
    api_client = get_docker_api_client(args)
    if not api_client:
        return
    docker_client = get_docker_client(args)
    if not docker_client:
        return
    if args.containers:
        check_containers(api_client, args.min, args.max)
    elif args.ping:
        check_ping(api_client)
    elif args.swarm:
        check_swarm(api_client)
    elif args.swarm_manager:
        check_swarm_manager(api_client)
    elif args.swarm_service:
        for service in args.swarm_service:
            check_swarm_service(docker_client, service)
    elif args.swarm_services:
        check_swarm_services(docker_client)

if __name__ == '__main__':
    perform_checks(sys.argv[1:])
    print_results()
    exit(rc)
