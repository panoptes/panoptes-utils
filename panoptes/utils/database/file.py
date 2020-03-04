import os
from warnings import warn
from contextlib import suppress
from uuid import uuid4
from glob import glob

from .. import error
from ..serializers import to_json
from ..serializers import from_json
from ..database import AbstractPanDB
from ..database import create_storage_obj


class PanFileDB(AbstractPanDB):
    """Stores collections as files of JSON records."""

    def __init__(self, db_name='panoptes', **kwargs):
        """Flat file storage for json records

        This will simply store each json record inside a file corresponding
        to the type. Each entry will be stored in a single line.
        Args:
            db_name (str, optional): Name of the database containing the collections.
        """

        super().__init__(db_name=db_name, **kwargs)

        self.db_folder = db_name

        # Set up storage directory.
        self._storage_dir = os.path.join(os.environ['PANDIR'], 'json_store', self.db_folder)
        os.makedirs(self._storage_dir, exist_ok=True)

    def insert_current(self, collection, obj, store_permanently=True):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        current_fn = self._get_file(collection, permanent=False)
        result = obj_id

        try:
            # Overwrite current collection file with obj.
            to_json(obj, filename=current_fn, append=False)
        except Exception as e:
            raise error.InvalidSerialization(f"Problem serializing object for insertion: {e} {current_fn} {obj!r}")

        if not store_permanently:
            return result
        else:
            return self.insert(collection, obj)

    def insert(self, collection, obj):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        collection_fn = self._get_file(collection)
        try:
            # Insert record into file
            to_json(obj, filename=collection_fn)
            return obj_id
        except Exception as e:
            raise error.InvalidSerialization(f"Problem inserting object into collection: {e}, {obj!r}")

    def get_current(self, collection):
        current_fn = self._get_file(collection, permanent=False)

        try:
            with open(current_fn) as f:
                msg = from_json(f.read())

            return msg
        except FileNotFoundError:
            self.logger.warning("No record found for {}".format(collection))
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
            name = '{}.json'.format(collection)
        else:
            name = 'current_{}.json'.format(collection)
        return os.path.join(self._storage_dir, name)

    def _make_id(self):
        return str(uuid4())

    @classmethod
    def permanently_erase_database(cls, db_name):
        # Clear out any .json files.
        storage_dir = os.path.join(os.environ['PANDIR'], 'json_store', db_name)
        for f in glob(os.path.join(storage_dir, '*.json')):
            os.remove(f)
