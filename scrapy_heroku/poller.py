from scrapyd.poller import QueuePoller

from util import get_spider_queues

class PgQueuePoller(QueuePoller):
  def update_projects(self):
    self.queues = get_spider_queues(self.config)