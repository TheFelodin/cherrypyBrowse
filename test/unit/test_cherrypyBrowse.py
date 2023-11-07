import os

import cherrypy
import pytest
import requests
from bs4 import BeautifulSoup

from cherrypyBrowse import TableApp

base_url = 'http://127.0.0.1:8082'
HEAD1 = 'name'
HEAD2 = 'street'
NAME1 = 'otto'
NAME2 = 'maier'
STREET1 = 'Landstr'
STREET2 = 'Hauptstr'
csv_text = f"{HEAD1},{HEAD2}\n{NAME1},{STREET1}\n{NAME2},{STREET2}\n{NAME1},{STREET2}"


@pytest.fixture(scope="module", autouse=True)
def cherrypy_server(tmp_path_factory):
    """
    Creating a cherrypt server with port based on provided base_url for testing purposes. Server is shut down after
    tests.

    Args:
        tmp_path_factory: session-scoped fixture to create arbitrary temporary directories

    Returns: directory of temporary files used by server

    """

    # creates temporary file for testing
    tmp_path = tmp_path_factory.mktemp("data")
    csv_filename = tmp_path / "test_data.csv"
    csv_filename.write_text(csv_text)

    # create server
    cherrypy.config.update({'server.socket_port': int(base_url[-4:])})
    cherrypy.tree.mount(TableApp(csv_filename), '/')
    cherrypy.engine.start()

    yield tmp_path  # jump into actual unittest (and come back here afterwards ...) while providing path to temp files.

    cherrypy.engine.exit()


@pytest.fixture(autouse=True)
def reset_db():
    """
    Resets the server for each test.
    """

    response = requests.get(base_url + '/reset_data')
    assert response.status_code == 200


def test_render_template():
    """
    Test if template is running on server
    """

    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check <th>-Elements for expected values
    assert "name" in soup.find('th', id='name').get_text()
    assert "street" in soup.find('th', id='street').get_text()


def test_index():
    """
    Test if server is running and base url is available.
    """

    response = requests.get(base_url)
    assert response.status_code == 200


def test_index_with_filter():
    """
    Test if an existing filter is showing the right results.
    """

    url = f'{base_url}/?filter={NAME2}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    data_table = soup.find("table", class_="data_table")
    tr = data_table.find('tr', id='1')

    # check csv_text string against HTML table content
    assert NAME2 in tr.find('td', id='name1').get_text()
    assert STREET2 in tr.find('td', id='street1').get_text()


def test_insert_data():
    """
    Tests if data provided in the correct format is added correctly.
    """

    insert_name = 'weber'
    insert_street = 'waldstr'
    insert = f'{{"name": "{insert_name}", "street": "{insert_street}"}}'
    url = f'{base_url}/insert_data?data={insert}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    data_table = soup.find("table", class_="data_table")
    tr = data_table.find_all('tr')[-1]
    id_value = tr.get("id")
    assert insert_name in tr.find('td', id=('name' + id_value)).get_text()
    assert insert_street in tr.find('td', id=('street' + id_value)).get_text()


def test_invalid_json_insert_data():
    """
    Tests if data provided in the wrong format raises the correct error message.
    """

    insert_name = 'weber'
    insert_street = 'waldstr'
    insert = f'"name": {insert_name}, "street": {insert_street}'
    url = f'{base_url}/insert_data?data={ {insert} }'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No valid JSON-data was given:" in soup.find("div", {"id": "error_message"}).get_text()


def test_empty_insert_data():
    """
    Tests if inserting without input raises the correct error message.
    """

    url = f'{base_url}/insert_data?data='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No input detected.Please enter valid JSON." in soup.find("div", {"id": "error_message"}).get_text()


def test_update_data():
    """
    Tests if updating data with correct filter is done right.
    """

    update_name = 'otto'
    update_street = 'waldstr'
    update = f'{{"name": "{update_name}", "street": "{update_street}"}}'
    url = f'{base_url}/update_data?data={update}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    data_table = soup.find("table", class_="data_table")

    # Create dictionaries to store the values
    name_values = {}
    street_values = {}

    # Iterate through the ResultSet
    for tr in data_table.find_all("tr"):
        td_name = tr.find("td", class_="name")
        td_street = tr.find("td", class_="street")
        if td_name and td_street:
            name_values[td_name['id']] = td_name.get_text()
            street_values[td_street['id']] = td_street.get_text()

    # Check if the values are as expected
    assert name_values['name1'] and name_values["name3"] == update_name
    assert street_values['street1'] and street_values['street3'] == update_street


def test_invalid_json_update_data():
    """
    Tests if invalid data causes update to produce the correct error message.
    """

    update_name = 'weber'
    update_street = 'waldstr'
    update = f'"name": {update_name}, "street": {update_street}'
    url = f'{base_url}/update_data?data={ {update} }'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No valid JSON-data was given:" in soup.find("div", {"id": "error_message"}).get_text()


def test_empty_update_data():
    """
    Tests if updating without input raises the correct error message.
    """

    url = f'{base_url}/update_data?data='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No input detected.Please enter valid JSON." in soup.find("div", {"id": "error_message"}).get_text()


def test_wrong_update_data():
    """
    Tests if updating with wrong input raises the correct error message.
    """

    url = f'{base_url}/update_data?data="frank"'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "'name' is missing." in soup.find("div", {"id": "error_message"}).get_text()


def test_delete_data_with_filter():
    """
    Tests deleting entries based on filter.
    """

    url = f'{base_url}/delete_data?filter={NAME1}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    data_table = soup.find("table", class_="data_table")
    tr = data_table.find('tr', id='1')

    # check csv_text string against HTML table content
    assert NAME2 in tr.find('td', id='name1').get_text()
    assert STREET2 in tr.find('td', id='street1').get_text()


def test_delete_data_without_filter():
    """
    Tests deleting all data if no filter is given.
    """

    url = f'{base_url}/delete_data?filter='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No entries found." in soup.find("div", {"id": "error_message"}).get_text()


def test_copy_file(cherrypy_server):
    """
    Tests if backup file was created.

    Args:
        cherrypy_server: Temporary path used by cherrypy server.
    """

    backup_file_path = cherrypy_server / "../data0/test_data.backup"
    assert backup_file_path.exists()


def test_reset_data(cherrypy_server):
    """
    Tests if reset_data restores deleted data file.

    Args:
        cherrypy_server: Temporary path used by cherrypy server.
    """

    file_path = cherrypy_server / "../data0"
    os.remove(file_path / "test_data.csv")
    reset_url = base_url + '/reset_data'
    response = requests.get(reset_url)
    file_path = cherrypy_server / "../data0/test_data.csv"
    assert file_path.exists()
    assert response.text == "Reset successful"


def test_reset_data_without_backup(cherrypy_server):
    """
    Tests if missing backup file causes correct error message in case of reset.

    Args:
        cherrypy_server: Temporary path used by cherrypy server.
    """

    backup_file_path = cherrypy_server / "../data0"
    os.remove(backup_file_path / "test_data.backup")
    reset_url = base_url + '/reset_data'

    res = requests.get(reset_url)
    assert res.status_code == 400
    assert "Backup file not found" in res.text
