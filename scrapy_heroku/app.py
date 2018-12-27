from os import environ

from twisted.application.service import Application
from twisted.application.internet import TimerService, TCPServer
from twisted.web import server
from twisted.python import log

from scrapyd.interfaces import (IEggStorage, IPoller, ISpiderScheduler,
    IEnvironment)
from scrapyd.launcher import Launcher
from scrapyd.environ import Environment
from scrapyd.eggstorage import FilesystemEggStorage
from scrapyd.website import Root

from poller import PgQueuePoller
from scheduler import PgScheduler


def application(config):
  app = Application('Scrapyd')
  port = int(environ.get('PORT', config.getint('http_port', 6800)))
  config.cp.set('scrapyd', 'database_url', environ.get('DATABASE_URL'))

  environment = Environment(config)
  poller = PgQueuePoller(config)
  scheduler = PgScheduler(config)
  eggstorage = FilesystemEggStorage(config)

  app.setComponent(IEnvironment, environment)
  app.setComponent(IPoller, poller)
  app.setComponent(ISpiderScheduler, scheduler)
  app.setComponent(IEggStorage, eggstorage)

  launcher = Launcher(config, app)
  timer = TimerService(5, poller.poll)
  webservice = TCPServer(port, server.Site(Root(config, app)))

  log.msg("Scrapyd web console available at http://localhost:%s/ (HEROKU)" % port)

  launcher.setServiceParent(app)
  timer.setServiceParent(app)
  webservice.setServiceParent(app)

  return app

