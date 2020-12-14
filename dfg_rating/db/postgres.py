import os

import psycopg2 as psql
from configparser import ConfigParser

from psycopg2.extras import DictCursor, execute_values

from dfg_rating import settings
from dfg_rating.settings import get_relative_path


class PostgreSQLDriver:
    def __init__(self, config=None, config_file='database.ini'):
        self.connection_params = None
        if config is None:
            self.connection_params = self.read_config_params(config_file)
            print(self.connection_params)
        self.connection = None
        #self.connect()
        pass

    def read_config_params(self, filename="database.ini", section='postgresql'):
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
        if self.connection is None:
            try:
                self.connection = psql.connect(**self.connection_params)
                cur = self.connection.cursor()
                cur.execute('SELECT version()')
                db_version = cur.fetchone()
                print(db_version)
                tables_list = self.execute_query(file_name=os.path.join("..", "data", "sql", "setup", "get_tables_list.sql"))
                print(f"Table lists {tables_list}")
                if len(tables_list) == 0:
                    self.execute_query(file_name=os.path.join("..", "data", "sql", "setup", "create_tables.sql"), commit=True)
            except (Exception, psql.DatabaseError) as error:
                print(error)

    def close(self):
        if self.connection is not None:
            self.connection.close()
            print('Database connection closed.')

    def execute_query(self, file_name=None, query=None, commit=False):
        if file_name is not None:
            try:
                cursor: DictCursor = self.connection.cursor(cursor_factory=DictCursor)
                sql_file = open(get_relative_path(file_name))
                cursor.execute(sql_file.read())
                sql_file.close()
                if commit:
                    self.connection.commit()
                return cursor.fetchall()
            except (Exception, psql.DatabaseError) as error:
                print(error)
        elif query is not None:
            try:
                cursor: DictCursor = self.connection.cursor(cursor_factory=DictCursor)
                cursor.execute(query)
                if commit:
                    self.connection.commit()
                return cursor.fetchall()
            except (Exception, psql.DatabaseError) as error:
                print(error)

    def insert_many(self, query_string, values):
        print(query_string)
        try:
            cursor: DictCursor = self.connection.cursor(cursor_factory=DictCursor)
            execute_values(cursor, query_string, values)
            #self.connection.commit()
        except (psql.errors.UniqueViolation) as e:
            print("Entity already exists")
        except (Exception, psql.DatabaseError) as error:
            print(error)
        finally:
            self.connection.commit()




