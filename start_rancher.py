import os
import subprocess
import time
import docker
import requests

from pprint import pprint
from requests.exceptions import ConnectionError

HOST = 'http://localhost'


class RancherServerAPI:

    RANCHER_SERVER_START_TIMEOUT = 100

    def __init__(self, url):
        self.url = url
        self.env_id = None

    def wait_for_startup(self):
        for k in range(0, self.RANCHER_SERVER_START_TIMEOUT):
            try:
                requests.get(self.url)
                break
            except ConnectionError:
                if k == 0:
                    print('Rancher server not running, waiting up to ' +
                          str(self.RANCHER_SERVER_START_TIMEOUT) +
                          's for rancher to start...')
                time.sleep(1)


    def create_environment(self):
        r = requests.post('/projects/${PROJECT_ID}/projects/${ID}?action=activate')
        pprint(r)

    def list_environments(self):
        r = requests.get(self.url + '/projects')
        content = r.json()

        envs = []
        for e in content['data']:
            envs.append({'id': e['id'],
                         'name': e['name'],
                         'healthState': e['healthState'],
                         'description': e['description']
                         })
        return envs


    def set_active_environment(self, env_id=None):
        envs = self.list_environments()
        env_info = None
        if env_id is None:
            self.env_id = envs[0]['id']
            env_info = envs[0]
        else:
            for e in envs:
                if envs[0]['id'] == env_id:
                    env_info = envs[0]
                    self.env_id = env_id

        if not env_info:
            print('Unable to set active environment.  Available environments are:')
            pprint(envs)
        else:
            print('Active Environment ID: ' + self.env_id)
            pprint(env_info)


    def add_host(self, hostname):
        payload = {'hostname': hostname}
        r = requests.post(self.url + '/projects/' + self.env_id + '/hosts', data=payload)
        content = r.json()
        pprint(content)

        pass



class RancherTestRig:

    RANCHER_SERVICE_IMG_DEFAULT_NAME = 'rancher/server:latest'
    RANCHER_SERVICE_CONTAINER_DEFAULT_NAME = 'rtr-rancher-server'

    RANCHER_PORT = 8080
    RANCHER_SERVER_START_TIMEOUT = 100

    def __init__(self,
                 rancher_host=None,
                 rancher_service_img_name=RANCHER_SERVICE_IMG_DEFAULT_NAME,
                 rancher_container_name=RANCHER_SERVICE_CONTAINER_DEFAULT_NAME
                 ):

        self.docker = docker.from_env()

        self.service_img_name = rancher_service_img_name
        self.service_container_name = rancher_container_name


        self.rancher_host = rancher_host
        self.server_container = self._get_container(self.service_container_name)
        self.rancher_server_api = RancherServerAPI(self.rancher_host + ':' + str(self.RANCHER_PORT) + '/v2-beta')


    def start_rancher_server(self, rebuild=False):
        print('Starting Rancher server...')

        # if the container does not exist, then start it
        if self.server_container is None:
            print('No ' + self.service_container_name + ' container exists.  Creating and starting...')
            self._create_and_start_server_container()
        else:
            if rebuild:
                print(self.service_container_name + ' container already exists.  ' +
                      'You requested to rebuild, so trashing and starting...')
                self.server_container.stop()
                self.server_container.remove()
                self._create_and_start_server_container()
            else:
                print(self.service_container_name + ' container already exists.  Restarting...')
                self.server_container.restart()


    def _get_container(self, name):
        try:
            return self.docker.containers.get(name)
        except docker.errors.NotFound:
            return None


    def _create_and_start_server_container(self):
        self._server_container = self.docker.containers.create(self.service_img_name,
                                                               name=self.service_container_name,
                                                               ports={self.RANCHER_PORT: self.RANCHER_PORT}
                                                               )
        self._server_container.start()
        print('created ' + self._server_container.id)





    def wait_for_server_to_start(self):
        self.rancher_server_api.wait_for_startup()





    def stop_server_container(self):
        print('Stopping Rancher server...')
        if self.service_container is None:
            print('No service container (' + self.service_container_name + ') exists.')
        else:
            self.service_container.stop()


    def basic_configuration(self):
        # 1) create environment

        self.rancher_server_api.set_active_environment()
        self.rancher_server_api.add_host('http://localhost')



    def set_rancher_host(self):
        rancher = self._get_rancher_client()
        res = rancher.create_project({"name":"rtr_test"})

        
        pprint(dir(res))
        pprint(res.id)
        #pprint(rancher.update_by_id_project({"name":"rtr_test"}))
        #{"activeValue":null,"id":"1as!api.host","inDb":false,"name":"api.host","source":null,"type":"activeSetting","value":"'$HOST':8080"}
        #pprint(dir(rancher))





rancherTestRig = RancherTestRig(rancher_host=HOST)

#rancherTestRig.start_rancher_server(rebuild=True)
#rancherTestRig.start_rancher_server()

rancherTestRig.wait_for_server_to_start()
rancherTestRig.basic_configuration()


#rancherTestRig.stop_server_container()





