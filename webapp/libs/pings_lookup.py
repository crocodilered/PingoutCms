from webapp.libs.abstract_lookup import AbstractLookup


class PingsLookup(AbstractLookup):
    """
    Class collects pings data and provides them by id as dicts
    """
    def key(self, ping):
        return ping["ping_id"]

    def val(self, ping):
        r = {
            "ping_id": ping["ping_id"],
            "user_id": ping["user_id"],
            "ts":      ping["ts"],
            "title":   ping["title"]
        }
        return r
