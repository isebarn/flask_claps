from __future__ import annotations

import copy
import inspect
import json
from datetime import datetime, date
from typing import List, Dict
from uuid import uuid4, UUID
from json import dumps

from app import db
from flask import current_app, g


def default_for_dumps(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()


class VersionedModel:
    """
    An Abstract Model Class that follows insert-only approach.
    Changes to an object result in a new version of that object being stored.
    To accomplish this, every object has 7 base following properties.
    """

    __abstract__ = True
    __empty_version__ = "00000000000000000000000000000000"

    entity_id: str
    version: str
    previous_version: str
    active: bool
    latest: bool
    changed_by_id: str
    changed_on: datetime

    def __init__(
        self,
        entity_id=None,
        version=None,
        previous_version=None,
        active=True,
        latest=True,
        changed_by_id=None,
        changed_on=None,
        *args,
        **kwargs,
    ):
        self.entity_id = entity_id
        self.version = version
        self.previous_version = previous_version
        self.active = active
        self.latest = latest
        self.changed_by_id = changed_by_id
        self.changed_on = changed_on

        [setattr(self, k, v) for k, v in kwargs.items()]

    @classmethod
    def annotations(cls):
        return list(VersionedModel.__annotations__.keys()) + list(
            cls.__annotations__.keys()
        )

    @classmethod
    def build_model(cls, model):
        o = cls()
        if model:
            for k, v in model.items():
                setattr(o, k, v)
            return o

    def create_in_database(self, cursor):
        try:
            # Create a new instance
            fieldnames = [x for x in self.annotations() if hasattr(self, x)]
            sql = "INSERT INTO {} ({}) VALUES ({})".format(
                self.__tablename__,
                ",".join(fieldnames),
                ",".join(["%s"] * len(fieldnames)),
            )

            cursor.execute(sql, tuple(getattr(self, x) for x in fieldnames))

        except Exception as e:
            traceback.print_exc()
            logging.error(cursor._last_executed)
            logging.error(f"Error in SQL:\n {e}")

    def create_multiple_in_database(self, cursor, data):
        raise NotImplementedError

    def update_from(self, other):
        if isinstance(other, self.__class__):
            if other.entity_id:
                self.entity_id = other.entity_id
            if other.version:
                self.version = other.version
        else:
            return False

    def get_new_from_scratch(self):
        if not self.entity_id:
            self.entity_id = uuid4().hex
        self.version = uuid4().hex
        self.previous_version = self.__empty_version__
        self.active = self.active if self.active is not None else True
        self.latest = True
        return self

    def get_new_from_existing(self):
        properties = self.get_as_dict()
        new_entity = self.__class__(**properties)
        new_entity.version = uuid4().hex
        new_entity.previous_version = self.version
        return new_entity

    def update_previous_records(self, cursor):
        sql = f"""UPDATE {self.__tablename__} SET latest = false WHERE entity_id = '{self.entity_id}';"""
        cursor.execute(sql)

    def save(self, connection=None, commit=True):
        new_entity = self.get_new_from_scratch()
        with current_app.app_context():
            if not connection:
                connection = db.connect

            with connection.cursor() as cursor:
                updated = False
                if self.entity_id and self.version:
                    updated = True
                    new_entity = self.get_new_from_existing()
                    self.update_previous_records(cursor)
                if not self.entity_id or not self.version:
                    new_entity = self.get_new_from_scratch()

                new_entity.create_in_database(cursor)

            if commit:
                connection.commit()
                operation = "update" if updated else "create"
                if cursor:
                    cursor.close()
            return new_entity

    @staticmethod
    def fetchone_dict(query, commit=True):
        with current_app.app_context():
            connection = db.connect
            with connection.cursor() as cursor:
                cursor.execute(query)
                desc = cursor.description
                results = cursor.fetchone()
                if results:
                    results = dict(zip([col[0] for col in desc], results))
            if commit:
                connection.commit()
                if cursor:
                    cursor.close()
            return results

    @staticmethod
    def fetchall_dict(query, commit=True):
        with current_app.app_context():
            connection = db.connect
            with connection.cursor() as cursor:
                cursor.execute(query)
                desc = cursor.description
                rows = cursor.fetchall()
                results = []
                if rows:
                    for row in rows:
                        results.append(dict(zip([col[0] for col in desc], row)))
            if commit:
                connection.commit()
                if cursor:
                    cursor.close()
            return results

    def get_as_dict(self, nested=False):
        params = dict()
        for k, val in self.__dict__.items():
            if k.startswith("_"):
                continue
            if isinstance(val, (date, datetime)):
                val = val.isoformat()
            if isinstance(val, VersionedModel) and nested:
                val = val.get_as_dict(nested=nested)
            params[k] = val
        return params

    def get_for_api(self, nested=True):
        data = self.get_as_dict(nested=nested)
        return data

    @classmethod
    def get(cls, value, key="entity_id"):
        query = f"""SELECT * FROM {cls.__tablename__} WHERE {key} = '{str(value)}' AND latest = true AND active = true;"""
        model = cls.fetchone_dict(query)
        o = cls()
        if model:
            for k, v in model.items():
                setattr(o, k, v)
            return o
        return None

    @classmethod
    def get_all(
        cls, fields: str, condition: str = "true", limit: int = None, offset: int = None
    ):
        default_condition = "latest = true AND active = true"
        condition = (
            condition + " AND " + default_condition if condition else default_condition
        )
        limit_query = f"LIMIT {limit}" if limit else ""
        offset_query = f"OFFSET {offset}" if offset else ""
        query = f"""SELECT {fields} FROM {cls.__tablename__} WHERE {condition} {limit_query} {offset_query};"""
        models = cls.fetchall_dict(query)
        for model in models:
            if model:
                o = cls()
                for k, v in model.items():
                    setattr(o, k, v)
                yield o

    def delete(self, connection=None, commit=True):
        with current_app.app_context():
            if not connection:
                connection = db.connect
            with connection.cursor() as cursor:
                new_entity = self.get_new_from_existing()
                self.update_previous_records(cursor)
                new_entity.active = False
                new_entity.create_in_database(cursor)

            if commit:
                connection.commit()
                operation = "delete"
                pusher_client.trigger(
                    f"{self.__tablename__}", operation, new_entity.get_for_api()
                )
                if cursor:
                    cursor.close()
            return new_entity
