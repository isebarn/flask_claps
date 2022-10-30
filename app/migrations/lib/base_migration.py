from app import db, create_app


class BaseMigration:
    def __init__(self):
        self.connection = None
        self.app = create_app()
        with self.app.app_context():
            self.connection = db.connect

    def _does_column_exist(self, table_name, column_name):
        schema_name = self.app.config.get('MYSQL_DATABASE')
        query = f"""
        SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE 
                TABLE_SCHEMA = '{schema_name}' 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}';
        """
        response = self.execute(query)
        return response[0][0] > 0

    def add_column(self, table_name, column_name, datatype):
        if self._does_column_exist(table_name, column_name):
            self.app.logger.info(f"Column {column_name} for table {table_name} already exists. Skipping creation...")
            return
        query = f"""ALTER TABLE {table_name} ADD {column_name} {datatype};"""
        self.execute(query)

    def drop_column(self, table_name, column_name):
        if not self._does_column_exist(table_name, column_name):
            self.app.logger.info(f"Column {column_name} for table {table_name} does not exist. Skipping deletion...")
            return
        query = f"""ALTER TABLE {table_name} DROP {column_name};"""
        self.execute(query)

    def alter_index(self, table_name, new_index_name, new_indexed_column, old_index_name):
        query = f"""ALTER TABLE {table_name} ADD INDEX {new_index_name} ({new_indexed_column}), DROP INDEX {old_index_name};"""
        self.execute(query)

    def alter_column(self, table_name, column_name, datatype):
        query = f"""ALTER TABLE {table_name} MODIFY COLUMN {column_name} {datatype};"""
        self.execute(query)

    def change_column_name(self, table_name, old_column_name, new_column_name):
        query = f"""ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name};"""
        self.execute(query)

    def change_table_name(self, old_table, new_table):
        query = f"""ALTER TABLE {old_table} RENAME TO {new_table};"""
        self.execute(query)

    def create_table(self, table_name, fields_with_type, drop_if_exists=True):
        if drop_if_exists:
            drop_query = f"""DROP TABLE IF EXISTS {table_name};"""
            self.execute(drop_query)
        create_query = f"""CREATE TABLE {table_name} ({fields_with_type});"""
        self.execute(create_query)

    def drop_table(self, table_name):
        query = f"""DROP TABLE {table_name};"""
        self.execute(query)

    def insert_db_version_data(self):
        query = f"INSERT INTO db_version (version) VALUES (0000000000);"
        self.execute(query)

    def update_version_table(self, version):
        query = f"UPDATE db_version SET version = {version};"
        self.execute(query)

    def execute(self, query):
        result = None
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            if cursor.rowcount:
                result = cursor.fetchall()
        self.connection.commit()
        return result

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection.cursor:
            self.connection.cursor.close()
