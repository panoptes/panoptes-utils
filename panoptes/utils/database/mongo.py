import pymongo
import weakref
from bson.objectid import ObjectId
from contextlib import suppress
from pymongo.errors import ConnectionFailure

from panoptes.utils.database import AbstractPanDB
from panoptes.utils.database import create_storage_obj

_shared_mongo_clients = weakref.WeakValueDictionary()


def get_shared_mongo_client(host, port, connect):
    global _shared_mongo_clients
    key = (host, port, connect)

    # Try to get previously stored client.
    with suppress(KeyError):
        return _shared_mongo_clients[key]

    # No client available, try to create new one.
    client = pymongo.MongoClient(host, port, connect=connect)
    try:
        # See second Note in official api docs for MongoClient
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
    except ConnectionFailure:  # pragma: no cover
        raise ConnectionError(f'Mongo server not available')

    _shared_mongo_clients[key] = client
    return client


class PanMongoDB(AbstractPanDB):
    def __init__(self, db_name='panoptes', host='localhost', port=27017, connect=False, **kwargs):
        """Connection to the running MongoDB instance

        This is a collection of parameters that are initialized when the unit
        starts and can be read and updated as the project is running. The server
        is a wrapper around a mongodb collection.

        Note:
            Because mongo can create collections at runtime, the pymongo module
            will also lazily create both databases and collections based off of
            attributes on the client. This means the attributes do not need to
            exist on the client object beforehand and attributes assigned to the
            object will automagically create a database and collection.

            Because of this, we manually store a list of valid collections that
            we want to access so that we do not get spuriously created collections
            or databases.

        Args:
            db_name (str, optional): Name of the database containing the collections.
            host (str, optional): hostname running MongoDB.
            port (int, optional): port running MongoDb.
            connect (bool, optional): Connect to mongo on create, defaults to True.

        Raises:
            ConnectionError: If the mongod server is not available.
        """

        super().__init__(**kwargs)

        # Get the mongo client.
        self._client = get_shared_mongo_client(host, port, connect)

        # Create an attribute on the client with the db name.
        db_handle = self._client[db_name]

        # Setup static connections to the collections we want.
        for collection in self.collection_names:
            # Add the collection as an attribute.
            setattr(self, collection, getattr(db_handle, collection))

    def insert_current(self, collection, obj, store_permanently=True):
        self.validate_collection(collection)
        obj = create_storage_obj(collection, obj)
        try:
            # Update `current` record. If one doesn't exist, insert one. This
            # combo is known as UPSERT (i.e. UPDATE or INSERT).
            upsert = True
            obj_id = self.current.replace_one({'type': collection}, obj, upsert).upserted_id
            if not store_permanently and not obj_id:
                # There wasn't a pre-existing record, so upserted_id was None.
                obj_id = self.get_current(collection)['_id']
        except Exception as e:
            self._warn("Problem inserting object into current collection: {}, {!r}".format(e, obj))
            obj_id = None

        if store_permanently:
            try:
                col = getattr(self, collection)
                obj_id = col.insert_one(obj).inserted_id
            except Exception as e:
                self._warn("Problem inserting object into collection: {}, {!r}".format(e, obj))
                obj_id = None

        if obj_id:
            return str(obj_id)
        return None

    def insert(self, collection, obj):
        self.validate_collection(collection)
        try:
            obj = create_storage_obj(collection, obj)
            # Insert record into db
            col = getattr(self, collection)
            return col.insert_one(obj).inserted_id
        except Exception as e:
            self._warn("Problem inserting object into collection: {}, {!r}".format(e, obj))
            return None

    def get_current(self, collection):
        return self.current.find_one({'type': collection})

    def find(self, collection, obj_id):
        collection = getattr(self, collection)
        if isinstance(obj_id, str):
            obj_id = ObjectId(obj_id)
        return collection.find_one({'_id': obj_id})

    def clear_current(self, type):
        self.current.delete_one({'type': type})

    @classmethod
    def permanently_erase_database(self, db_name):
        # Create an instance of PanMongoDb in order to get access to
        # the relevant client.
        db = PanMongoDB(db_type='mongo', db_name=db_name)
        for collection_name in db.collection_names:
            if not hasattr(db, collection_name):
                db._warn(f'Unable to locate collection {collection_name!r} to erase it.')
                continue
            try:
                collection = getattr(db, collection_name)
                collection.drop()
            except Exception as e:
                db._warn(f'Unable to drop collection {collection_name!r}; exception: {e}.')
