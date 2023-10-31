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
    # creates temporary file for testing
    tmp_path = tmp_path_factory.mktemp("data")
    csv_filename = tmp_path / "test_data.csv"
    csv_filename.write_text(csv_text)
    cherrypy.config.update({'server.socket_port': int(base_url[-4:])})
    cherrypy.tree.mount(TableApp(csv_filename), '/')
    cherrypy.engine.start()

    yield tmp_path  # jump into actual unittest (and come back here afterwards ...) while providing path to temp files.

    cherrypy.engine.exit()


@pytest.fixture(autouse=True)
def reset_db():
    response = requests.get(base_url + '/reset_data')
    assert response.status_code == 200


def test_cherrypy_server():
    response = requests.get(base_url)
    assert response.status_code == 200


def test_render_template():
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Check <th>-Elements for expected values
    assert "name" in soup.find('th', id='name').get_text()
    assert "street" in soup.find('th', id='street').get_text()


def test_index():
    response = requests.get(base_url)
    assert response.status_code == 200


def test_index_with_filter():
    url = f'{base_url}/?filter={NAME2}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    data_table = soup.find("table", class_="data_table")
    tr = data_table.find('tr', id='1')

    # check csv_text string against HTML table content
    assert NAME2 in tr.find('td', id='name1').get_text()
    assert STREET2 in tr.find('td', id='street1').get_text()


def test_insert_data():
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
    insert_name = 'weber'
    insert_street = 'waldstr'
    insert = f'"name": {insert_name}, "street": {insert_street}'
    url = f'{base_url}/insert_data?data={ {insert} }'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No valid JSON-data was given:" in soup.find("div", {"id": "error_message"}).get_text()


def test_empty_insert_data():
    url = f'{base_url}/insert_data?data='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No input detected.Please enter valid JSON." in soup.find("div", {"id": "error_message"}).get_text()


def test_update_data():
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
    update_name = 'weber'
    update_street = 'waldstr'
    update = f'"name": {update_name}, "street": {update_street}'
    url = f'{base_url}/update_data?data={ {update} }'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No valid JSON-data was given:" in soup.find("div", {"id": "error_message"}).get_text()


def test_empty_update_data():
    url = f'{base_url}/update_data?data='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No input detected.Please enter valid JSON." in soup.find("div", {"id": "error_message"}).get_text()


def test_delete_data_with_filter():
    url = f'{base_url}/delete_data?filter={NAME1}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    data_table = soup.find("table", class_="data_table")
    tr = data_table.find('tr', id='1')

    # check csv_text string against HTML table content
    assert NAME2 in tr.find('td', id='name1').get_text()
    assert STREET2 in tr.find('td', id='street1').get_text()


def test_delete_data_without_filter():
    url = f'{base_url}/delete_data?filter='
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    assert "No entries found." in soup.find("div", {"id": "error_message"}).get_text()


def test_copy_file(tmp_path):
    backup_file_path = tmp_path / "../data0/test_data.backup"
    assert backup_file_path.exists()


def test_reset_data():
    reset_url = base_url + '/reset_data'
    response = requests.get(reset_url)
    assert response.text == "Reset successful"


def test_reset_data_without_backup(tmp_path):
    backup_file_path = tmp_path / "../data0"
    print("\nZZZZZZZZZZZ", os.listdir(backup_file_path))
    os.remove(backup_file_path/"test_data.backup")
    print("AAAAAAaaAAAAA", os.listdir(backup_file_path))
    reset_url = base_url + '/reset_data'

    # Use pytest.raises to catch the expected exception
    with pytest.raises(cherrypy.HTTPError) as exc_info:
        requests.get(reset_url)
    print("BBBBBBBBBBBBBB", os.listdir(backup_file_path))
    exception = exc_info.value
    assert exception.status == 400
    assert str(exception) == "Backup file not found"
