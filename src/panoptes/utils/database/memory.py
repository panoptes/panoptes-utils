import threading
import weakref
from contextlib import suppress
from uuid import uuid4

from panoptes.utils import error
from panoptes.utils.database import AbstractPanDB
from panoptes.utils.database.base import create_storage_obj
from panoptes.utils.serializers import from_json
from panoptes.utils.serializers import to_json


class PanMemoryDB(AbstractPanDB):
    """In-memory store of serialized objects.

    We serialize the objects in order to test the same code path used
    when storing in an external database.
    """

    active_dbs = weakref.WeakValueDictionary()

    @classmethod
    def get_or_create(cls, db_name=None, **kwargs):
        """Returns the named db, creating if needed.

        This method exists because PanDB gets called multiple times for
        the same database name. With mongo or a file store where the storage
        is external from the instance, that is not a problem, but with
        PanMemoryDB the instance is the store, so the instance must be
        shared."""
        db = PanMemoryDB.active_dbs.get(db_name)
        if not db:
            db = PanMemoryDB(db_name=db_name, **kwargs)
            PanMemoryDB.active_dbs[db_name] = db
        return db

    def __init__(self, **kwargs):
        """Initialize in-memory database.
        
        Args:
            **kwargs: Additional keyword arguments passed to parent class.
        """
        super().__init__(**kwargs)
        self.current = {}
        self.collections = {}
        self.lock = threading.Lock()

    def _make_id(self):
        """Generate a unique ID for database objects.
        
        Returns:
            str: Unique identifier string.
        """
        return str(uuid4())

    def insert_current(self, collection, obj, store_permanently=True):
        """Insert object as current item in collection.
        
        Args:
            collection (str): Collection name to insert into.
            obj: Object to insert.
            store_permanently (bool): Whether to also store in permanent collection.
            
        Returns:
            str: Object ID of inserted item.
        """
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id)
        try:
            obj = to_json(obj)
        except Exception as e:
            raise error.InvalidSerialization(
                f"Problem serializing object for insertion: {e} {obj!r}"
            )

        with self.lock:
            self.current[collection] = obj
            if store_permanently:
                self.collections.setdefault(collection, {})[obj_id] = obj
        return obj_id

    def insert(self, collection, obj):
        """Insert object into collection.
        
        Args:
            collection (str): Collection name to insert into.
            obj: Object to insert.
            
        Returns:
            str: Object ID of inserted item.
        """
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id)
        try:
            obj = to_json(obj)
        except Exception as e:
            raise error.InvalidSerialization(
                f"Problem inserting object into collection: {e}, {obj!r}"
            )

        with self.lock:
            self.collections.setdefault(collection, {})[obj_id] = obj
        return obj_id

    def get_current(self, collection):
        """Get current object from collection.
        
        Args:
            collection (str): Collection name to get current from.
            
        Returns:
            dict or None: Current object in collection, or None if not found.
        """
        with self.lock:
            obj = self.current.get(collection, None)
        if obj:
            obj = from_json(obj)
        return obj

    def find(self, collection, obj_id):
        """Find object by ID in collection.
        
        Args:
            collection (str): Collection name to search in.
            obj_id (str): Object ID to find.
            
        Returns:
            dict or None: Found object, or None if not found.
        """
        with self.lock:
            obj = self.collections.get(collection, {}).get(obj_id)
        if obj:
            obj = from_json(obj)
        return obj

    def clear_current(self, entry_type):
        """Clear current entry for specified type.
        
        Args:
            entry_type (str): Entry type to clear.
        """
        with suppress(KeyError):
            del self.current[entry_type]

    @classmethod
    def permanently_erase_database(cls, *args, **kwargs):
        """Permanently erase the database.
        
        For testing purposes only. Erases all data and references.
        
        Args:
            *args: Positional arguments (ignored).
            **kwargs: Keyword arguments (ignored).
        """
        # For some reason we're not seeing all the references disappear
        # after tests. Perhaps there is some global variable pointing at
        # the db or one of its referrers, or perhaps a pytest fixture
        # hasn't been removed.
        PanMemoryDB.active_dbs = weakref.WeakValueDictionary()
