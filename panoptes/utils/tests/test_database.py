import pytest

from panoptes.utils.database import PanDB
from panoptes.utils import error


def test_bad_db():
    with pytest.raises(Exception):
        PanDB('foobar')


def test_insert_and_no_permanent(db):
    rec = {'test': 'insert'}
    id0 = db.insert_current('config', rec, store_permanently=False)

    record = db.get_current('config')
    assert record['data']['test'] == rec['test']

    record = db.find('config', id0)
    assert record is None


def test_insert_and_get_current(db):
    rec = {'test': 'insert'}
    db.insert_current('config', rec)

    record = db.get_current('config')
    assert record['data']['test'] == rec['test']


def test_clear_current(db):
    rec = {'test': 'insert'}
    db.insert_current('config', rec)

    record = db.get_current('config')
    assert record['data']['test'] == rec['test']

    db.clear_current('config')

    record = db.get_current('config')
    assert record is None


def test_simple_insert(db):
    rec = {'test': 'insert'}
    # Use `insert` here, which returns an `ObjectId`
    id0 = db.insert('config', rec)

    record = db.find('config', id0)
    assert record['data']['test'] == rec['test']


def test_bad_insert(db):
    """Can't serialize `db` properly so gives warning and returns nothing."""
    with pytest.raises(error.InvalidSerialization):
        rec = db.insert_current('config', db, store_permanently=False)
        assert rec is None

    with pytest.raises(error.InvalidSerialization):
        rec = db.insert('config', db)
        assert rec is None


@pytest.mark.filterwarnings('ignore')
def test_bad_collection(db):
    with pytest.raises(error.InvalidCollection):
        db.insert_current('foobar', {'test': 'insert'})

    with pytest.raises(error.InvalidCollection):
        db.insert('foobar', {'test': 'insert'})


def test_warn_bad_object(db):
    with pytest.raises(error.InvalidSerialization):
        db.insert_current('observations', {'junk': db})

    with pytest.raises(error.InvalidSerialization):
        db.insert('observations', {'junk': db})
