import os
from contextlib import suppress
from glob import glob
from uuid import uuid4

from loguru import logger
from panoptes.utils import error
from panoptes.utils.database import AbstractPanDB
from panoptes.utils.database.base import create_storage_obj
from panoptes.utils.serializers import from_json
from panoptes.utils.serializers import to_json


class PanFileDB(AbstractPanDB):
    """Stores collections as files of JSON records."""

    def __init__(self, db_name='panoptes', storage_dir='json_store', **kwargs):
        """Flat file storage for json records.

        This will simply store each json record inside a file corresponding
        to the type. Each entry will be stored in a single line.

        Args:
            db_name (str, optional): Name of the database containing the collections.
            storage_dir (str, optional): The name of the directory where the
                database files will be stored. Default is `json_store` in current
                directory. Pass an absolute path for non-relative.
        """

        super().__init__(db_name=db_name, **kwargs)

        self.db_folder = db_name

        # Set up storage directory.
        self.storage_dir = os.path.join(storage_dir, self.db_folder)
        os.makedirs(self.storage_dir, exist_ok=True)

    def insert_current(self, collection, obj, store_permanently=True):
        obj_id = self._make_id()
        result = obj_id
        storage_obj = create_storage_obj(collection, obj, obj_id)
        current_fn = self._get_file(collection, permanent=False)

        try:
            # Overwrite current collection file with obj.
            to_json(storage_obj, filename=current_fn, append=False)
        except Exception as e:
            raise error.InvalidSerialization(f"Problem serializing before insert: {e!r} {obj!r}")

        if store_permanently:
            result = self.insert(collection, obj)

        return result

    def insert(self, collection, obj):
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id)
        collection_fn = self._get_file(collection)
        try:
            # Insert record into file
            to_json(obj, filename=collection_fn)
            return obj_id
        except Exception as e:
            raise error.InvalidSerialization(f"Problem serializing before insert: {e!r} {obj!r}")

    def get_current(self, collection):
        current_fn = self._get_file(collection, permanent=False)

        try:
            with open(current_fn) as f:
                msg = from_json(f.read())

            return msg
        except FileNotFoundError:
            logger.warning(f"No record found for {collection}")
            return None

    def find(self, collection, obj_id):
        collection_fn = self._get_file(collection)
        obj = None
        with suppress(FileNotFoundError):
            with open(collection_fn, 'r') as f:
                for line in f:
                    if obj_id in line:
                        obj = from_json(line)
                        break

        return obj

    def clear_current(self, record_type):
        """Clears the current record of the given type.

        Args:
            record_type (str): The record type, e.g. 'weather', 'environment', etc.
        """
        current_f = self._get_file(record_type, permanent=False)
        with suppress(FileNotFoundError):
            os.remove(current_f)

    def _get_file(self, collection, permanent=True):
        if permanent:
            name = f'{collection}.json'
        else:
            name = f'current_{collection}.json'
        return os.path.join(self.storage_dir, name)

    def _make_id(self):
        return str(uuid4())

    @classmethod
    def permanently_erase_database(cls, db_name, storage_dir=None):
        # Clear out any .json files.
        storage_dir = os.path.join(storage_dir, db_name)
        for f in glob(os.path.join(storage_dir, '*.json')):
            os.remove(f)
