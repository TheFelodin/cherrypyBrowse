import cherrypy
import requests
import threading
import pytest

from bs4 import BeautifulSoup
from cherrypyBrowse.cherrypyBrowse import TableApp

base_url = 'http://127.0.0.1:8082'


@pytest.fixture()
def start_cherrypy(scope=module, autouse=True):
    cherrypy.config.update({'server.socket_host': '127.0.0.1', 'server.socket_port': 8082})
    cherrypy.tree.mount(TableApp('some-file.csv'), '/')
    cherrypy.engine.start()

    def stop():
        cherrypy.engine.exit()
        cherrypy.engine.block()

    t = threading.Thread(target=stop)
    t.start()
    yield
    t.join()


def test_cherrypy_server(cherrypy_server):
    response = requests.get('http://127.0.0.1:8082')
    assert response.status_code == 200


def test_webpage_content():
    url = base_url
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check <th>-Elements for expected values
    assert "name" in soup.find('th', id='name').get_text()
    assert "street" in soup.find('th', id='street').get_text()


def test_webpage_content_filter():
    filter_value = 'otto'
    url = f'{base_url}/fetch_data?filter={filter_value}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tr = soup.find('tr', id='1')
    assert "Otto" in tr.find('td', id='name1').get_text()
    assert "Landstr" in tr.find('td', id='street1').get_text()
