import pymysql

connection = pymysql.connect(host='172.16.8.147',
                             port=3306,
                             user='dba',
                             passwd='123456',
                             db='greenbox',
                             cursorclass=pymysql.cursors.DictCursor,
                             charset='utf8mb4')
