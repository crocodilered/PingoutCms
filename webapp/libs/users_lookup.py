from webapp.libs.abstract_lookup import AbstractLookup


class UsersLookup(AbstractLookup):
    """
    Class collects users data and provides them by id as dicts
    """
    def key(self, user):
        return user["user_id"]

    def val(self, user):
        return {
            "user_id":        user["user_id"],
            "profile_name":   user["profile"]["name"] if "name" in user["profile"] else "",
            "profile_gender": user["profile"]["gender"] if "gender" in user["profile"] else "",
            "profile_age":    user["profile"]["age"] if "age" in user["profile"] else "",
            "profile_about":  user["profile"]["about"] if "about" in user["profile"] else "",
            "profile_avatar": user["profile"]["avatar_file_name"] if "avatar_file_name" in user["profile"] else "",
        }
