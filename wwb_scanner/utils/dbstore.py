import os
import datetime

from tinydb import TinyDB, where
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

APP_PATH = os.path.expanduser('~/wwb_scanner_data')

DB_PATH = os.path.join(APP_PATH, 'db.json')

class DBStore(object):
    TABLES = ['scan_configs', 'scans_performed', 'scans_imported']
    def __init__(self):
        if not os.path.exists(os.path.dirname(DB_PATH)):
            os.makedirs(os.path.dirname(DB_PATH))
        self.db = TinyDB(DB_PATH, storage=CachingMiddleware(JSONStorage))
    def add_scan_config(self, config, force_insert=False):
        if config.get('datetime') is None:
            config.datetime = datetime.datetime.utcnow()
        table = self.db.table('scan_configs')
        if True:#with table:
            if config.get('eid') is not None:
                dbconfig = table.get(eid=config.eid)
            else:
                dbconfig = table.get(where('datetime') == config.datetime)
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
        if True:#with table:
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
    def add_scan(self, spectrum, scan_config):
        if scan_config.get('eid') is None:
            self.add_scan_config(scan_config)
        data = spectrum._serialize()
        data['scan_config_eid'] = scan_config.eid
        table = self.db.table('scans_performed')
        if True:#with table:
            table.insert(data)
    def get_all_scans(self):
        table = self.db.table('scans_performed')
        if True:#with table:
            scans = table.all()
        return scans
    
db_store = DBStore()
