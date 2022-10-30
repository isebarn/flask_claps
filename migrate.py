from os import listdir
import argparse
import os
import sys
from importlib import import_module

from app import models
from app import db, create_app
from app.migrations.lib.run import create_migration_file
from app.migrations.lib.run import get_db_version
from app.migrations.lib.run import run_backward_migration_script
from app.migrations.lib.run import run_forward_migration_script
from app.migrations.lib.run import get_schema
from pymysql.err import ProgrammingError

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
MIGRATION_DIR = os.path.join(ROOT_PATH, "app", "migrations")
sys.path.append(MIGRATION_DIR)


def get_arg_parser():
    example_text = """example:
    %(prog)s -c True
    %(prog)s -rf True
    %(prog)s -rb True
    %(prog)s -db True
    """
    parser = argparse.ArgumentParser(
        prog="python migrate.py",
        epilog=example_text,
        description="Run for Database Migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--create_migration",
        help="create new migration file with predefined template",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-rf",
        "--run_forward_migration",
        help="Run forward migration",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-rb",
        "--run_backward_migration",
        help="Run backward migration",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-db", "--get_db_version", help="Get db version", type=bool, default=False
    )
    return parser


def main():
    models = [
        x for x in listdir("app/models") if x.endswith(".py") and x != "__init__.py"
    ]

    classes = {}
    for model in models:
        with open(f"app/models/{model}") as f:
            lines = [
                x.replace("class ", "").split("(")[0]
                for x in f.readlines()
                if x.startswith("class ")
            ]

            classes[model.replace(".py", "")] = lines

    models = []
    for key, value in classes.items():
        for model in value:
            models.append(getattr(import_module(f"app.models.{key}"), model))

    app = create_app()
    with app.app_context():
        connection = db.connect



        query = "describe {};"
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [x[0] for x in cursor.fetchall()]

            for model in models:
                if model.__tablename__ in tables:
                    cursor.execute(query.format(model.__tablename__))
                    results = cursor.fetchall()
                    fields = [x[0] for x in results]

                    pass

                else:
                    create = """
                        `entity_id` varchar(32) NOT NULL,
                        `version` varchar(32) NOT NULL,
                        `previous_version` varchar(32) DEFAULT '00000000000000000000000000000000',
                        `active` tinyint(1) DEFAULT '1',
                        `latest` tinyint(1) DEFAULT '1',
                        `changed_by_id` varchar(32) DEFAULT NULL,
                        `changed_on` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    """

                    for field, value in model.__annotations__.items():
                        v = value()
                        if isinstance(v, str) and field.endswith("_id"):
                            create += f"    `{field}` TEXT,\n"
                        elif isinstance(v, str):
                            create += f"    `{field}` TEXT,\n"
                        elif isinstance(v, int):
                            create += f"    `{field}` INTEGER,\n"
                        elif isinstance(v, bool):                         
                            create += f"    `{field}` TINYINT,\n"

                        from pprint import pprint
                    

                    create = create[0:-1]
                    create += """
                        PRIMARY KEY (`entity_id`,`version`),
                        INDEX latest_ind (`entity_id`,`latest`,`active`)                    
                    """

                    create = f"create table {model.__tablename__} (\n{create}\n)"
                    cursor.execute(create)

    # parser = get_arg_parser()
    # parsed = parser.parse_args()
    # db_version = get_db_version()
    # if parsed.create_migration:
    #     create_migration_file()
    # elif parsed.get_db_version:
    #     print(f'Current db version: {db_version}')
    # elif parsed.run_forward_migration:
    #     print(f'Current db version: {db_version}')
    #     run_forward_migration_script(old_db_version=db_version)
    # elif parsed.run_backward_migration:
    #     print(f'Current db version: {db_version}')
    #     run_backward_migration_script()
    # else:
    #     parser.print_help()


if __name__ == "__main__":
    main()
