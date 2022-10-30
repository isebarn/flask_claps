import os
from importlib import import_module

from app.migrations.lib.migration_template import get_template
from app.migrations.lib.read_db_vers import get_version

SCRIPTS_DIR = os.path.abspath(os.path.dirname(__file__))
MIGRATION_DIR = os.path.abspath(os.path.dirname(SCRIPTS_DIR))

def get_schema():
    pass

def _get_migration_scripts():
    script_versions = {
        file for file in os.listdir(MIGRATION_DIR) if file not in ["__init__.py", "lib", "__pycache__"]
    }
    return script_versions


def _get_forward_migration_script():
    db_version = get_db_version()
    for file in _get_migration_scripts():
        if file.strip().split('_')[1] == db_version:
            return file.strip().split('.')[0]


def _get_backward_migration_script():
    db_version = get_db_version()
    for file in _get_migration_scripts():
        if file.strip().split('_')[0] == db_version:
            return file.strip().split('.')[0]


def get_db_version():
    db_version = get_version() or '0000000000'
    return f'{int(db_version):010d}'


def create_migration_file():
    try:
        current_db_version = int(get_version())
    except:
        print('DB version not found in table!!!')
        return
    new_version = current_db_version + 1
    current_db_version = f'{current_db_version:010d}'
    new_version = f'{new_version:010d}'
    file_name = f"{new_version}_{current_db_version}_migration.py"
    template = get_template(new_version, current_db_version)
    with open(os.path.join(MIGRATION_DIR, file_name), 'w') as fp:
        fp.write(template)


def run_forward_migration_script(old_db_version):
    file = _get_forward_migration_script()
    if file is None:
        latest_db_version = get_db_version()
        if old_db_version == latest_db_version:
            print('Migration for current DB version not found!!!')
        else:
            print('Migration complete!!!')
            print(f'Latest DB version: {latest_db_version}')
        return
    print(f'Running forward migration: {file.strip().split("/")[-1]}')
    imported = import_module(f'{file}', package=None)
    imported.upgrade()
    return run_forward_migration_script(old_db_version)


def run_backward_migration_script():
    file = _get_backward_migration_script()
    if file is None:
        print('Migration for current DB version not found!!!')
        return
    print(f'Running backward migration: {file.strip().split("/")[-1]}')
    imported = import_module(f'{file}', package=None)
    imported.downgrade()
    print('Migration complete!!!')
    print(f'Latest DB version: {get_db_version()}')
