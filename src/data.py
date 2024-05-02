import json
import sqlite3
from uuid import uuid4
import hashlib


def create_table(cur):
    table_aire = """CREATE TABLE IF NOT EXISTS aire (id INTEGER PRIMARY KEY, age_min INTEGER, age_max INTEGER, polygone_type TEXT, nom TEXT, surface REAL, nombre_de_jeux INTEGER)"""
    cur.execute(table_aire)
    table_aire_geo = """CREATE TABLE IF NOT EXISTS aire_geo (id INTEGER, lat REAL, lon REAL, FOREIGN KEY (id) REFERENCES aire (id))"""
    cur.execute(table_aire_geo)


def existing_tables(cur):
    try:
        cur.execute("SELECT aire, aire_geo FROM sqlite_master WHERE type='table'")
        return True
    except sqlite3.OperationalError:
        return False


class MoteurDB:
    def __init__(self):
        self.conn = sqlite3.connect('aires_de_jeux.sq3', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        # Si les tables existent déjà on passe cette étape
        if not existing_tables(cur):
            create_table(cur)
            self.conn.commit()
        # On récupère les clefs hashées du fichiers JSON
        with open('clefs.json', 'r') as hashed_keys_file:
            self.hashed_keys = json.load(hashed_keys_file)

        cur.execute("SELECT COUNT(id) FROM aire")
        self.nombre_aires = cur.fetchall()[0][0]

    def authorize(self, key):
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return hash_key in self.hashed_keys

    def get_authorization(self):
        api_key = str(uuid4())
        hashed_api_keys = hashlib.md5(api_key.encode()).hexdigest()
        self.hashed_keys.append(hashed_api_keys)
        with open('clefs.json', 'w') as hashed_keys_file:
            json.dump(self.hashed_keys, hashed_keys_file)
        return api_key

    def get_schema(self, key):
        if not self.authorize(key):
            return 'You are not authorized to access this at the moment, please enter your API key'

        cursor = self.conn.cursor()

        cursor.execute("PRAGMA table_info('aire')")
        columns = cursor.fetchall()

        column_names = [column[1] for column in columns]

        return column_names

    def get_aires(self, key: str, champs: str, condition: str):
        if not self.authorize(key):
            return 'You are not authorized to access this at the moment, please enter your API key'

        cursor = self.conn.cursor()

        if condition is None:
            cursor.execute(f"SELECT {champs} FROM aire")
        else:
            cursor.execute(f"SELECT {champs} FROM aire WHERE {condition}")

        aires = list(cursor.fetchall())

        return aires

    def close(self):
        self.conn.close()