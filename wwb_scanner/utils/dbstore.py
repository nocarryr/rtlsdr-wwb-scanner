import os
import datetime

import tinydb
from tinydb import TinyDB, where

from wwb_scanner.utils import numpyjson

APP_PATH = os.path.expanduser('~/wwb_scanner_data')

class JSONStorage(tinydb.JSONStorage):
    def read(self):
        # Get the file size
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            # File is empty
            return None
        else:
            self._handle.seek(0)
            return numpyjson.load(self._handle)
    def write(self, data):
        self._handle.seek(0)
        serialized = numpyjson.dumps(data)
        self._handle.write(serialized)
        self._handle.flush()
        self._handle.truncate()

class DBStore(object):
    DB_PATH = os.path.join(APP_PATH, 'db.json')
    SCAN_DB_PATH = os.path.join(APP_PATH, 'scan_db.json')
    TABLES = ['scan_configs', 'scans_performed', 'scans_imported']
    def __init__(self):

        self._db = None
        self._scan_db = None
        #self.migrate_db()
    @property
    def db(self):
        db = self._db
        if db is None:
            self._check_dirs()
            db = self._db = TinyDB(self.DB_PATH, storage=JSONStorage)
        return db
    @property
    def scan_db(self):
        db = self._scan_db
        if db is None:
            self._check_dirs()
            db = self._scan_db = TinyDB(self.SCAN_DB_PATH, storage=JSONStorage)
        return db
    def _check_dirs(self):
        if not os.path.exists(os.path.dirname(self.DB_PATH)):
            os.makedirs(os.path.dirname(self.DB_PATH))
        if not os.path.exists(os.path.dirname(self.SCAN_DB_PATH)):
            os.makedirs(os.path.dirname(self.SCAN_DB_PATH))
    def migrate_db(self):
        for table_name in ['scans_performed', 'scans_imported']:
            if table_name not in self.db.tables():
                continue
            print('migrating table "{}"'.format(table_name))
            old_table = self.db.table(table_name)
            new_table = self.scan_db.table(table_name)
            eids = []
            for item in old_table.all():
                eids.append(item.eid)
                new_table.insert(item)
            old_table.remove(eids=eids)
            self.db.purge_table(table_name)
    def add_scan_config(self, config, force_insert=False):
        if config.get('datetime') is None:
            config['datetime'] = datetime.datetime.utcnow()
        table = self.db.table('scan_configs')
        if config.get('eid') is not None:
            dbconfig = table.get(eid=config.eid)
        else:
            dbconfig = table.get(where('datetime') == config['datetime'])
        if dbconfig is not None:
            if force_insert:
                eids = [dbconfig.eid]
                table.update(config._serialize(), eids=eids)
            eid = dbconfig.eid
        else:
            eid = table.insert(config._serialize())
        config.eid = eid
    def get_scan_config(self, **kwargs):
        table = self.db.table('scan_configs')
        if kwargs.get('datetime'):
            dbconfig = table.get(where('datetime')==kwargs.get('datetime'))
        elif kwargs.get('eid'):
            dbconfig = table.get(eid=kwargs.get('eid'))
        elif kwargs.get('name'):
            dbconfig = table.get(where('name')==kwargs.get('name'))
        elif table._last_id > 0:
            dbconfig = table.get(eid=table._last_id)
        else:
            dbconfig = None
        return dbconfig
    def add_scan(self, spectrum, scan_config=None):
        if scan_config is None:
            scan_config = spectrum.scan_config
        if scan_config is not None:
            if scan_config.get('eid') is None:
                self.add_scan_config(scan_config)
            spectrum.scan_config_eid = scan_config.eid
        data = spectrum._serialize()
        table = self.scan_db.table('scans_performed')
        if spectrum.eid is not None:
            eid = spectrum.eid
            table.update(data, eids=[eid])
        else:
            eid = table.insert(data)
            spectrum.eid = eid
        return eid
    def get_all_scans(self):
        table = self.scan_db.table('scans_performed')
        scans = table.all()
        scan_data = {}
        for scan in scans:
            excluded = ['samples', 'sample_data', 'center_frequencies']
            scan_data[scan.eid] = {key:scan[key] for key in scan.keys()
                                    if key not in excluded}
        return scan_data
    def get_scan(self, eid):
        table = self.scan_db.table('scans_performed')
        return table.get(eid=eid)
    def update_scan(self, eid, **kwargs):
        table = self.scan_db.table('scans_performed')
        table.update(kwargs, eids=[eid])

db_store = DBStore()
