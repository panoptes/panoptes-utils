import abc
from warnings import warn

from panoptes.utils import current_time
from panoptes.utils.library import load_module


def _get_db_class(module_name='file'):
    """Load the main DB class for the module of the given name.

    .. doctest:

        >>> _get_db_class()
        <class 'panoptes.utils.database.file.PanFileDB'>
        >>> _get_db_class('memory')
        <class 'panoptes.utils.database.memory.PanMemoryDB'>

    Args:
        module_name (str): Name of module, one of: `file` (default), 'memory'.

    Returns:
        `panoptes.utils.database.PanDB`: An instance of the db class for the correct database type.

    Raises:
        Exception: If an unsupported database type string is passed.
    """
    class_map = {
        'file': 'PanFileDB',
        'memory': 'PanMemoryDB',
    }

    full_module_name = f'panoptes.utils.database.{module_name}'

    try:
        db_module = load_module(full_module_name)
        return getattr(db_module, class_map[module_name])
    except Exception:
        raise Exception(f'Unsupported database type: {full_module_name}')


class AbstractPanDB(metaclass=abc.ABCMeta):
    def __init__(self, db_name=None, collection_names=list(), logger=None, **kwargs):
        """
        Init base class for db instances.

        Args:
            db_name: Name of the database, typically panoptes or panoptes_testing.
            collection_names (list of str): Names of the valid collections.
            logger: (Optional) logger to use for warnings.
        """
        self.logger = logger
        if self.logger:
            self.logger.info(f'Creating PanDB {db_name} with collections: {collection_names}')
        self.db_name = db_name
        self.collection_names = collection_names

    def _warn(self, *args, **kwargs):
        if self.logger:
            self.logger.warning(*args, **kwargs)
        else:
            warn(*args)

    def validate_collection(self, collection):
        if collection not in self.collection_names:
            msg = 'Collection type {!r} not available'.format(collection)
            self._warn(msg)
            # Can't import panoptes.utils.error earlier
            from panoptes.utils.error import InvalidCollection
            raise InvalidCollection(msg)

    @abc.abstractclassmethod
    def insert_current(self, collection, obj, store_permanently=True):  # pragma: no cover
        """Insert an object into both the `current` collection and the collection provided.

        Args:
            collection (str): Name of valid collection within the db.
            obj (dict or str): Object to be inserted.
            store_permanently (bool): Whether to also update the collection,
                defaults to True.

        Returns:
            str: identifier of inserted record. If `store_permanently` is True, will
                be the identifier of the object in the `collection`, otherwise will be the
                identifier of object in the `current` collection. These may or
                may not be the same.
                Returns None if unable to insert into the collection.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def insert(self, collection, obj):  # pragma: no cover
        """Insert an object into the collection provided.

        The `obj` to be stored in a collection should include the `type`
        and `date` metadata as well as a `data` key that contains the actual
        object data. If these keys are not provided then `obj` will be wrapped
        in a corresponding object that does contain the metadata.

        Args:
            collection (str): Name of valid collection within the db.
            obj (dict or str): Object to be inserted.

        Returns:
            str: identifier of inserted record in `collection`.
                Returns None if unable to insert into the collection.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_current(self, collection):  # pragma: no cover
        """Returns the most current record for the given collection

        Args:
            collection (str): Name of the collection to get most current from

        Returns:
            dict|None: Current object of the collection or None.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def find(self, collection, obj_id):  # pragma: no cover
        """Find an object by it's identifier.

        Args:
            collection (str): Collection to search for object.
            obj_id (ObjectID|str): Record identifier returned earlier by insert
                or insert_current.

        Returns:
            dict|None: Object matching identifier or None.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def clear_current(self, type):  # pragma: no cover
        """Clear the current record of a certain type

        Args:
            type (str): The type of entry in the current collection that
                should be cleared.
        """
        raise NotImplementedError


def create_storage_obj(collection, data, obj_id=None):
    """Returns the object to be stored in the database"""
    obj = dict(data=data, type=collection, date=current_time(datetime=True))
    if obj_id:
        obj['_id'] = obj_id
    return obj


class PanDB(object):
    """Simple class to load the appropriate DB type based on the config.

    We don't actually create instances of this class, but instead create
    an instance of the 'correct' type of db.
    """

    def __new__(cls, db_type='memory', db_name=None, *args, **kwargs):
        """Create an instance based on db_type."""

        collection_names = PanDB.collection_names()

        # Load the correct DB module
        DB = _get_db_class(db_type)

        if db_type == 'memory':
            # The memory type has special setup
            db_instance = DB.get_or_create(collection_names=collection_names, **kwargs)
        else:
            db_instance = DB(collection_names=collection_names, **kwargs)

        return db_instance

    @staticmethod
    def collection_names():
        """The pre-defined list of collections that are valid."""
        return [
            'camera_board',
            'control_board',
            'camera_env_board',
            'control_env_board',
            'config',
            'current',
            'drift_align',
            'environment',
            'mount',
            'observations',
            'offset_info',
            'power',
            'safety',
            'state',
            'telemetry_board',
            'weather',
        ]

    @classmethod
    def permanently_erase_database(cls,
                                   db_type,
                                   db_name,
                                   really=False,
                                   dangerous=False,
                                   *args, **kwargs):
        """Permanently delete the contents of the identified database."""

        if not isinstance(db_name, str) or 'test' not in db_name:
            raise ValueError(
                'permanently_erase_database() called for non-test database {!r}'.format(db_name))

        if really != 'Yes' or dangerous != 'Totally':
            raise Exception('PanDB.permanently_erase_database called with invalid args!')

        # Load the correct DB module.
        DB = _get_db_class(db_type)

        # Do the deletion.
        DB.permanently_erase_database(db_name, *args, **kwargs)
