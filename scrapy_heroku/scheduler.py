from scrapyd.scheduler import SpiderScheduler

from util import get_spider_queues

class PgScheduler(SpiderScheduler):
  def __init__(self, config):
    self.config = config
    self.update_projects()

  def update_projects(self):
    self.queues = get_spider_queues(self.config)
