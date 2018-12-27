from scrapyd.utils import get_project_list

from queue import PgQueue

def get_spider_queues(config):
  """Return a dict of Spider Queues keyed by project name"""
  queues = {}
  for project in get_project_list(config):
    table = 'scrapy_%s_queue' % project
    queues[project] = PgQueue(config, table=table)
  return queues