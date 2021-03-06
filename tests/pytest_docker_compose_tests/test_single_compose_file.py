import time
import requests
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

import pytest

pytest_plugins = ["docker_compose"]


@pytest.fixture(scope="module")
def wait_for_api(module_scoped_container_getter):
    """Wait for the api from my_api_service to become responsive"""
    request_session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    request_session.mount('http://', HTTPAdapter(max_retries=retries))

    service = module_scoped_container_getter.get("my_api_service").network_info[0]
    api_url = "http://%s:%s/" % (service.hostname, service.host_port)
    assert request_session.get(api_url)

    start = time.time()
    while 'Exit' not in module_scoped_container_getter.get("my_short_lived_service").human_readable_state:
        if time.time() - start >= 5:
            raise RuntimeError(
                'my_short_lived_service should spin up, echo "Echoing" and '
                'then shut down, since it still running something went wrong'
            )
        time.sleep(.5)

    return request_session, api_url


@pytest.mark.compose_file_path
def test_read_all(wait_for_api):
    request_session, api_url = wait_for_api
    assert len(request_session.get(urljoin(api_url, 'items/all')).json()) == 0


if __name__ == '__main__':
    pytest.main(['-m', 'compose_file_path', '--docker-compose', './my_network/docker-compose.yml', '--docker-compose-no-build'])
