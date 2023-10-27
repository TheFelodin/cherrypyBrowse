import requests
from bs4 import BeautifulSoup

base_url = 'http://localhost:8081'

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
