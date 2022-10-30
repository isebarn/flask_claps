def get_template(new_version, current_db_version):
    return f"""
from lib.base_migration import BaseMigration

revision = "{new_version}"
down_revision = "{current_db_version}"

migration = BaseMigration()


def upgrade():
    # write migration here
    migration.update_version_table(version=revision)


def downgrade():
    # write migration here
    migration.update_version_table(version=down_revision)

"""
