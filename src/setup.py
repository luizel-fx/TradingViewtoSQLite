from database_setup import *
from load_initial_data import *

def setup(symbol_dict):
    create_db()
    scrapps_and_save(symbol_dict)