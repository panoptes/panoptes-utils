from google.cloud import firestore

from panoptes.utils import error
from panoptes.utils import current_time
from panoptes.utils.database import AbstractPanDB
from panoptes.utils.config.client import get_config


class PanFireStoreDB(AbstractPanDB):
    def __init__(self, **kwargs):
        """Firestore storage.

        Note:
            Assumes an active internet connection
        """

        super().__init__(**kwargs)

        unit_id = get_config('pan_id', default=None)

        if unit_id is None:
            raise error.PanError(msg="No pan_id given in config, can't save to firestore.")

        # Get the mongo client.
        self._client = firestore.Client()

        # Hold the current item for each collection.
        self._current = dict()

        # Setup static connections to the collections we want.
        for collection in self.collection_names:
            # Set an attribute equal to the name that points to collection reference
            setattr(self, collection, self._client.collection(f'units/{unit_id}/{collection}'))

            self._current[collection] = None

    def insert_current(self, collection, obj, store_permanently=True):
        if store_permanently:
            document_info = self.insert(collection, obj)
            # Add the server generated timestamp.
            obj['date'] = document_info[0].ToJsonString()
        else:
            # Add local time if we don't hit server.
            obj['date'] = current_time(datetime=True)

        # Store our current collection
        self._current[collection] = obj

    def insert(self, collection, obj):
        """Add the document to the given collection.

        Args:
            collection (str): The name of the collection, must be a valid collection.
            obj (dict): A dict object containing the information to add.

        Returns:
            tuple|None: Returned by the firestore server: timestamp and document reference.
        """
        self.validate_collection(collection)
        try:
            obj = self.create_storage_obj(collection, obj)

            # Insert record into db
            collection = getattr(self, collection)

            return collection.add(obj)
        except Exception as e:
            self._warn("Problem inserting object into collection: {}, {!r}".format(e, obj))
            return None

    def get_current(self, collection):
        """Get the current object either from dict or firebase server.

        This method looks in an in-memory dict for the value corresponding to
        `collection`:
            * If the item is a dict-like object, it is returned.
            * If the item is a `firestore.DocumentReference` then the item will
                be fetched from the server.
            * If the item is `None`, the server will be queried for the most
                recent item for the given collection.

        Args:
            collection (str): Name of the collection.

        Returns:
            dict: The most recent object for the collection.
        """
        obj = self._current[collection]

        # If we don't have an object or a ref, look up from server.
        if obj is None:
            collection = getattr(self, collection)
            try:
                obj = next(collection.order_by('date').limit(1).stream()).to_dict()
            except StopIteration:
                obj = None

        if isinstance(obj, firestore.DocumentReference):
            # Pull from server.
            obj = obj.get().to_dict()

        return obj

    def find(self, collection, obj_id):
        collection = getattr(self, collection)
        return collection.document(obj_id).get().to_dict()

    def clear_current(self, type):
        pass

    def create_storage_obj(self, collection, data, obj_id=None):
        """Returns the object to be stored in the database"""
        data['date'] = firestore.SERVER_TIMESTAMP

        return data
