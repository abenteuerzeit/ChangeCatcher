import pymysql


class Repositories:
    def __init__(self):
        self.host = "172.16.8.147"
        self.port = 3306
        self.user = "dba"
        self.passwd = "123456"
        self.db = "farfetch"
        self.charset = 'utf8mb4'
        self.cursorclass = pymysql.cursors.DictCursor,
        self.repositories = []

    def connect(self, host=None,
                port=None,
                user=None,
                passwd=None,
                db=None):
        self.host = host or self.host
        self.port = port or self.port
        self.user = user or self.user
        self.passwd = passwd or self.passwd
        self.db = db or self.db

        for repository in self.repositories:
            repository.connect()

    def add(self, repository):
        print "repository:", repository.__class__
        self.repositories.append(repository)


repositories = Repositories()


class Repository:
    def __init__(self,
                 host=None,
                 port=None,
                 user=None,
                 passwd=None,
                 db=None,
                 cursorclass=pymysql.cursors.DictCursor,
                 charset='utf8mb4'):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.db = db
        self.connection = None
        self.charset = charset
        self.cursorclass = cursorclass
        repositories.add(self)

    def connect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

        db = self.db or repositories.db
        user = self.user or repositories.user
        host = self.host or repositories.host
        port = self.port or repositories.port
        cursorclass = self.cursorclass or repositories.cursorclass
        passwd = self.passwd or repositories.passwd
        charset = self.charset or repositories.charset

        print "connect to %s@%s:%s - %s" % (user, host, port, db)

        self.connection = pymysql.connect(host=host,
                                          port=port,
                                          user=user,
                                          passwd=passwd,
                                          db=db,
                                          cursorclass=cursorclass,
                                          charset=charset)
