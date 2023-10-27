import cherrypy
import requests
import threading
import pytest

from bs4 import BeautifulSoup
<<<<<<<< HEAD:test/unit/test_cherrypyBrowse.py
from src.cherrypyBrowse.cherrypyBrowse import TableApp
========
from cherrypyBrowse.cherrypyBrowse import TableApp
>>>>>>>> origin/Restructured:test/unit/test_main.py

base_url = 'http://127.0.0.1:8082'


@pytest.fixture(scope="module")
def cherrypy_server(tmp_path_factory):
    # Erstellen Sie eine temporäre CSV-Datei für Testzwecke
    tmp_path = tmp_path_factory.mktemp("data")
    csv_filename = tmp_path / "test_data.csv"
    csv_filename.write_text("""\
                                name,street
                                otto,Landstr
                                maier,Hauptstr
                                """)

    cherrypy.config.update({'server.socket_host': '127.0.0.1', 'server.socket_port': 8082})
    cherrypy.tree.mount(TableApp(csv_filename), '/')
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
