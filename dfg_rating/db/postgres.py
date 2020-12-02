import psycopg2 as psql
from configparser import ConfigParser

from dfg_rating import settings


class PostgreSQLDriver:
    def __init__(self, config=None, config_file='database.ini'):
        self.connection_params = None
        if config is None:
            self.connection_params = self.read_params(config_file)
        self.connection = None
        self.connect()
        pass

    def read_params(self, filename="database.ini", section='postgresql'):
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(settings.get_relative_path(filename))
        print(list(parser.keys()))

        # get section, default to postgresql
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception(f"Section {section} not found in the {filename} file")

        return db

    def connect(self):
        try:
            self.connection = psql.connect(**self.connection_params)
            cur = self.connection.cursor()
            print('PostgreSQL datbase version:')
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            print(db_version)
            cur.close()
        except (Exception, psql.DatabaseError) as error:
            print(error)
        finally:
            if self.connection is not None:
                self.connection.close()
                print('Database connection closed.')
