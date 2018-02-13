from webapp.libs.abstract_lookup import AbstractLookup


class UsersLookup(AbstractLookup):
    """
    Class collects users data and provides them by id as dicts
    """
    def key(self, user):
        return user["user_id"]

    def val(self, user):
        r = {
            "user_id": user["user_id"],
            "name":    user["profile"]["name"]
        }
        if "gender" in user["profile"]:
            r["profile_gender"] = user["profile"]["gender"]
        if "age" in user["profile"]:
            r["profile_age"] = user["profile"]["age"]
        return r
