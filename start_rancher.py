import os
import subprocess
import time
import gdapi

from pprint import pprint
from requests.exceptions import ConnectionError
from docker import Client as DockerClient

DOCKER_HOST = 'unix://var/run/docker.sock'
HOST = 'http://localhost'

class RancherTestRig:

    RANCHER_SERVICE_CONTAINER_NAME = 'rtr-rancher-server'
    RANCHER_PORT = 8080
    RANCHER_SERVER_START_TIMEOUT = 100

    def __init__(
                self,
                docker_host = None,
                rancher_host = None,
                rancher_service_img_name = None
            ):
        self.docker = DockerClient(base_url=docker_host)
        self.rancher_service_img_name = 'rancher/server'
        self.rancher = None
        self.rancher_host = rancher_host

        print('RANCHER_HOST'+self.rancher_host)


    def start_rancher_server_container(self, rebuild_container=False):
        print('Starting Rancher server...')
        service_container = self._get_container_by_name(self.RANCHER_SERVICE_CONTAINER_NAME)

        # if the container does not exist, then start it
        if service_container is None:
            print('No '+self.RANCHER_SERVICE_CONTAINER_NAME+' container exists.  Creating and starting...')
            self._create_rancher_server_container_and_start()
        else:
            containerId = service_container['Id']
            if rebuild_container:
                print(self.RANCHER_SERVICE_CONTAINER_NAME+' container already exists.  You requested to rebuild, so trashing and starting...')
                self.docker.stop(container=containerId)
                self.docker.remove_container(container=containerId)
                self._create_rancher_server_container_and_start()

            else:
                print(self.RANCHER_SERVICE_CONTAINER_NAME+' container already exists.  Restarting...')
                self.docker.restart(container=containerId)


    def _get_container_by_name(self, name):
        filters = { 'name': name }
        service_containers = self.docker.containers(all=True, filters=filters)
        if len(service_containers) == 0:
            return None
        elif len(service_containers) == 1:
            return service_containers[0]
        else:
            raise ValueError('Error: multiple containers with name: '+name+' exists.  Not sure how that is possible.')


    def _create_rancher_server_container_and_start(self):
        c = self.docker.create_container(
                                image=self.rancher_service_img_name,
                                name=self.RANCHER_SERVICE_CONTAINER_NAME,
                                ports=[self.RANCHER_PORT],
                                host_config = self.docker.create_host_config(
                                        port_bindings={self.RANCHER_PORT:self.RANCHER_PORT}
                                    )
                            )
        self.docker.start(container=c['Id'])
        print('created ' + c['Id'])
        return c


    def _get_rancher_client(self):
        if not self.rancher:
            for i in range(0, self.RANCHER_SERVER_START_TIMEOUT):
                try:
                    self.rancher = gdapi.Client(url=self.rancher_host + ':' + str(self.RANCHER_PORT) + '/v1')
                    break
                except ConnectionError:
                    if i==0:
                        print('Rancher server not running, waiting up to '+
                                str(self.RANCHER_SERVER_START_TIMEOUT)+
                                's for rancher to start...')
                    time.sleep(1)
        return self.rancher


    def wait_for_rancher_server_to_start(self):
        rancher = self._get_rancher_client()
       

    def stop_rancher_server_container(self):
        print('Stopping Rancher server...')
        service_container = self._get_container_by_name(self.RANCHER_SERVICE_CONTAINER_NAME)

        # if the container does not exist, then start it
        if service_container is None:
            print('No '+self.RANCHER_SERVICE_CONTAINER_NAME+' container exists.')
        else:
            containerId = service_container['Id']
            self.docker.stop(container=containerId)


    #def create_rancher_project(self):



    def set_rancher_host(self):
        rancher = self._get_rancher_client()
        res = rancher.create_project({"name":"rtr_test"})

        
        pprint(dir(res))
        pprint(res.id)
        #pprint(rancher.update_by_id_project({"name":"rtr_test"}))
        #{"activeValue":null,"id":"1as!api.host","inDb":false,"name":"api.host","source":null,"type":"activeSetting","value":"'$HOST':8080"}
        #pprint(dir(rancher))





rancherTestRig = RancherTestRig(docker_host=DOCKER_HOST, rancher_host=HOST)

#rancherTestRig.start_rancher_server_container(rebuild_container=True)
rancherTestRig.wait_for_rancher_server_to_start()

rancherTestRig.set_rancher_host()


#rancherTestRig.stop_rancher_server_container()