from libre_api import *
from libre_bot import Contract

def test_create_client():
    client = create_client(True)

def test_get_reports():
    contracts = [Contract(name="Бородин Ростислав Алексеевич", birthday="27/4/1994")]
    send_reports(contracts)

def test_prepare_last_file():
    prepare_last_file()