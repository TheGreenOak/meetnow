import redis


class RedisDictDB:
    def __init__(self, prefix=None):
        self.prefix = prefix
        self.db = redis.Redis(decode_responses=True)
    

    def __getitem__(self, key):
        """
        Implementation for the [] operator.
        """
        retVal = self.db.hgetall(f"{self.prefix if self.prefix else ''}{':' if self.prefix else ''}{key}")

        if retVal:
            return retVal
        return None
    

    def __setitem__(self, key, value):
        """
        Implementation for the [] = operator.
        """
        self.db.hmset(f"{self.prefix if self.prefix else ''}{':' if self.prefix else ''}{key}", value)
    

    def __delitem__(self, key):
        """
        Implementation for the del operator.
        """
        self.db.delete(f"{self.prefix if self.prefix else ''}{':' if self.prefix else ''}{key}")