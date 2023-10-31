from rediscluster import StrictRedisCluster


class RedisTaskScheduler:
    def __init__(self):
        self.redis = None

    def connect(self, nodes=[{"host": "172.16.8.147", "port": "6379"}]):
        print "connect to redis cluster:", nodes
        self.redis = StrictRedisCluster(startup_nodes=nodes, decode_responses=True)

    def push(self, name, task):
        # print "push task:" + task
        self.redis.lpush(name, task)

    def pop(self, name):
        return self.redis.rpop(name)

    def length(self, name):
        return self.redis.llen(name)

    def get(self, name):
        return self.redis.get(name)


if __name__ == "__main__":
    print ""
