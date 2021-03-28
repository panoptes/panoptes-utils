import abc

from loguru import logger
from panoptes.utils.library import load_module
from panoptes.utils.time import current_time


def create_storage_obj(collection, data, obj_id):
    """Wrap the data in a dict along with the id and a timestamp."""
    return dict(_id=obj_id, data=data, type=collection, date=current_time(datetime=True))


def get_db_class(module_name='file'):
    """Load the main DB class for the module of the given name.

    .. note::

        This is used by the `PanDB` constructor to determine the
        correct database type. Normal DB instantiation should be done
        via the `PanDB()` class with the desired `db_type` parameter
        set.  See example in `PanDB` below.

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
    except Exception as e:
        raise Exception(f'Unsupported database type: {full_module_name}: {e!r}')


class AbstractPanDB(metaclass=abc.ABCMeta):
    def __init__(self, db_name=None, **kwargs):
        """
        Init base class for db instances.

        Args:
            db_name: Name of the database, typically 'panoptes' or 'panoptes_testing'.
        """
        self.db_name = db_name
        logger.info(f'Creating PanDB {self.db_name}')

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
    def get_current(self, collection):  # pragma: no cover
        """Returns the most current record for the given collection

        Args:
            collection (str): Name of the collection to get most current from

        Returns:
            dict|None: Current object of the collection or None.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def find(self, collection, obj_id):  # pragma: no cover
        """Find an object by it's identifier.

        Args:
            collection (str): Collection to search for object.
            obj_id (ObjectID|str): Record identifier returned earlier by insert
                or insert_current.

        Returns:
            dict|None: Object matching identifier or None.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def clear_current(self, type):  # pragma: no cover
        """Clear the current record of a certain type

        Args:
            type (str): The type of entry in the current collection that
                should be cleared.
        """
        raise NotImplementedError()


class PanDB(object):
    """Simple class to load the appropriate DB type based on the config.

    We don't actually create instances of this class, but instead create
    an instance of the 'correct' type of db.

    .. doctest:

        >>> from panoptes.utils.database import PanDB
        >>> type(PanDB(db_type='file'))
        <class 'panoptes.utils.database.file.PanFileDB'>
        >>> type(PanDB('memory'))
        <class 'panoptes.utils.database.memory.PanMemoryDB'>

        >>> # Make a new instance of the db.
        >>> memory_db = PanDB(db_type='memory')
        >>> # Returns None if noe record.
        >>> memory_db.get_current('safety')

        >>> insert_id = memory_db.insert_current('safety', True)
        >>> record = memory_db.get_current('safety')
        >>> record['data']
        True
    """

    def __new__(cls, db_type='memory', db_name=None, *args, **kwargs):
        """Create an instance based on db_type."""

        # Load the correct DB module
        DatabaseModule = get_db_class(db_type)

        if db_type == 'memory':
            # The memory type has special setup
            db_instance = DatabaseModule.get_or_create(**kwargs)
        else:
            db_instance = DatabaseModule(**kwargs)

        return db_instance

    @classmethod
    def permanently_erase_database(cls,
                                   db_type,
                                   db_name,
                                   storage_dir=None,
                                   really=False,
                                   dangerous=False,
                                   *args, **kwargs):
        """Permanently delete the contents of the identified database."""

        if not isinstance(db_name, str) or 'test' not in db_name:
            raise ValueError(f'permanently_erase_database() called for non-test database {db_name!r}')

        if really != 'Yes' or dangerous != 'Totally':
            raise Exception('PanDB.permanently_erase_database called with invalid args!')

        # Load the correct DB module and do the deletion.
        get_db_class(db_type).permanently_erase_database(db_name, storage_dir=storage_dir, *args, **kwargs)
