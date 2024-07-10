import couchdb


class CouchDBUtil:
    def __init__(self, server, city_name):
        self.db = couchdb.Server(server)[f'osm_tags_cache_osmium_{city_name}']

    def save_node(self, elem, overwrite=False):
        try:
            self.db.save({'tags': elem[1], '_id': str(elem[0]), 'type': 'point'})
        except couchdb.http.ResourceConflict:
            if overwrite:
                self.db.save({'tags': elem[1], '_id': str(elem[0]), 'type': 'point'})

    def save_area(self, elem, overwrite=False):
        try:
            self.db.save({'tags': elem[1], 'area': elem[2], '_id': str(elem[0]), 'type': 'area'})
        except couchdb.http.ResourceConflict:
            if overwrite:
                doc = self.db.get(str(elem[0]))
                doc = doc | {'tags': elem[1], 'area': elem[2], '_id': str(elem[0]), 'type': 'area'}
                self.db.save(doc)

    def save_park(self, park_dict, overwrite=True):
        try:
            self.db.save(park_dict)
        except couchdb.http.ResourceConflict:
            if overwrite:
                doc = self.db.get(park_dict['_id'])
                doc = doc | park_dict
                self.db.save(doc)
