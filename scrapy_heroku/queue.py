from scrapyd.interfaces import ISpiderQueue
from scrapyd.spiderqueue import SqliteSpiderQueue

import json
import urlparse
import psycopg2

class PgPriorityQueue(object):
  def __init__(self, config, table='scrapy_queue'):
    url = urlparse.urlparse(config.get('database_url'))
    # Remove query strings.
    path = url.path[1:]
    path = path.split('?', 2)[0]

    args = {
      'dbname': path,
      'user': url.username,
      'password': url.password,
      'host': url.hostname,
      'port': url.port,
    }

    conn_string = ' '.join('%s=%s' % item for item in args.items())

    self.conn_string = conn_string
    self.table = table
    self.conn = psycopg2.connect(conn_string)
    q = "create table if not exists %s " \
      "(id SERIAL primary key, " \
      " priority real, " \
      " message text);" % table
    self.__execute(q, results=False)
    self.conn.commit()

  def __execute(self, q, args=None, results=True):
    try:
      cursor = self.conn.cursor()
      cursor.execute(q, args)
    except (psycopg2.InterfaceError, psycopg2.OperationalError) as err:
      self.conn = psycopg2.connect(self.conn_string)
      cursor = self.conn.cursor()
      cursor.execute(q, args)

    if results:
      try:
        results = list(cursor)
      except psycopg2.ProgrammingError:
        results = []
    cursor.close()

    return results

  def put(self, message, priority=0.0):
    args = (priority, self.__encode(message))
    q = "insert into %s (priority, message) values (%%s,%%s);" % self.table
    self.__execute(q, args, results=False)
    self.conn.commit()

  def pop(self):
    q = "select id, message from %s order by priority desc limit 1 for update;" % self.table
    results = self.__execute(q)
    if len(results) == 0:
      return
    id_, msg = results[0]
    q = "delete from %s where id=%%s;" % self.table
    self._execute(q, (id_,), results=False)
    self.conn.commit()
    return self.__decode(msg)

  def remove(self, func):
    q = "select id, message from %s for update" % self.table
    n = 0
    for id_, msg in self.__execute(q):
      if func(self.__decode(msg)):
        q = "delete from %s where id=%%s" % self.table
        self.__execute(q, (id_,), results=False)
        n += 1
    self.conn.commit()
    return n

  def clear(self):
    self.__execute("delete from %s" % self.table, results=False)
    self.conn.commit()

  def __len__(self):
    q = "select count(*) from %s" % self.table
    result = self.__execute(q)[0][0]
    self.conn.commit()
    return result

  def __iter__(self):
    q = "select message, priority from %s order by priority desc" % self.table
    result = ((self.__decode(x), y) for x, y in self.__execute(q))
    self.conn.commit()
    return result

  def __encode(self, obj):
    return json.dumps(obj)

  def __decode(self, text):
    return json.loads(text)


class PgQueue(SqliteSpiderQueue):
  def __init__(self, config, table='scrapy_queue'):
    self.q = PgPriorityQueue(config, table)
  
