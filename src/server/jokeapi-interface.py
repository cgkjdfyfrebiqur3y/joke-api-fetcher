import requests
import json
class classproperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        return self.func(cls)

class BackendError(RuntimeError):
    pass
class BackendNotRunningError(BackendError):
    pass
class BackendNotConennctedError(BackendError):
    pass
class staticvalues:
    URL_PROGRAMMING = "https://v2.jokeapi.dev/joke/Programming?safe-mode"
    URL_MISCELLANEOUS = "https://v2.jokeapi.dev/joke/Misc?safe-mode"
    URL_CHRISTMAS = "https://v2.jokeapi.dev/joke/Christmas?safe-mode"
    URL_ANY = "https://v2.jokeapi.dev/joke/Any?safe-mode"
    @classproperty
    def URL_CUSTOM(cls, categories,type:bool):
        type_str = "twopart" if type == True else "single"
        if isinstance(categories, list):
            if len(categories) == 0:
                categories = "Any"
            for i in categories:
                if i not in ["Programming", "Misc", "Christmas","Spooky","Pun"]:
                    raise ValueError(f"Invalid category: {i}. Valid categories are: Programming, Misc, Christmas, Spooky, Pun")
            categories = ",".join(categories)
        if type == None:
            return f"https://v2.jokeapi.dev/joke/{categories}?safe-mode"
        return f"https://v2.jokeapi.dev/joke/{categories}?safe-mode&type={type_str}"
class JokeAPI:
    """
Class that represents the interface for the low dependency
"""
    def __init__(self,categories=["Programming", "Misc", "Christmas","Spooky","Pun"]):
        self.categories = categories
    def getjoke(self,type:bool = None,):
        """
Gets a joke from JokeAPI
"""
        url = staticmethod.URL_CUSTOM(self.categories,type)
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.ConnectionError:
            raise BackendNotRunningError("JokeAPI cannot be reached")
        except requests.exceptions.Timeout:
            raise BackendNotRunningError("JokeAPI timed out")
        if response.status_code == 200:
            data = json.loads(response.text)

            if data["type"] == "single":
                return data["joke"]
            elif data["type"] == "twopart":
                return f"{data['setup']} ... {data['delivery']}"
            else:
                raise BackendError("Backend broken")
        else:
            if str(response.status_code)[1] == "5":
                raise BackendError("Backend destroyed(do not use this program anymore) (backend failed)")
            elif str(response.status_code) == "410":
                raise BackendError("Backend destroyed(do not use this program anymore) (returned 410 Gone)")
            else:
                raise ConnectionError(f"Failed joke fetch ( status code: {response.status_code} )")
            


            