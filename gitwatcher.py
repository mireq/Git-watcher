# -*- coding: utf-8 -*-

import configparser
import os
import pyinotify
import re
from pyinotify import WatchManager, ThreadedNotifier
from subprocess import Popen, PIPE


class GitWatcher(object):
	def __init__(self):
		self.__stat_re = re.compile("([0-9]* )(\+*)(-*)")

	def watch(self):
		self.__git_command = ["git", "--git-dir", self.directory]

		mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO

		self.__wm = WatchManager()
		self.__wdd = self.__wm.add_watch(os.path.join(self.directory, 'refs', 'heads'), mask, rec = True)

		notifier = ThreadedNotifier(self.__wm, self.process_event)
		notifier.start()

	def process_event(self, event):
		(name, ext) = os.path.splitext(event.pathname)
		if ext == '.lock':
			return
		self.display_notify(self.get_commit_title(), self.get_commit_text())

	def display_notify(self, title, text):
		Popen(["notify-send", "-t", "3600000", "-a", "git", "-i", self.icon, "-u", "low", title, text])

	def call_git(self, arguments):
		return str(Popen(self.__git_command + arguments, stdin=PIPE, stdout=PIPE, stderr=PIPE).stdout.readall(), encoding="utf-8")

	def get_git_author(self):
		return self.call_git(["log", "-1", "--format='%an'"]).strip("\n")

	def get_git_description(self):
		return self.call_git(["log", "-1", "--format=%n<b>%s</b>%n%n%b"])

	def get_git_stat(self):
		return "<span font=\"monospace\">" + self.__stat_re.sub("\\1<span color=\"#00ff00\">\\2</span><span color=\"#ff0000\">\\3</span>", self.call_git(["diff", "--stat", 'HEAD^', 'HEAD'])) + "</span>"

	def get_commit_title(self):
		return "Commit from: " + self.get_git_author() + ", project: " + self.project

	def get_commit_text(self):
		return self.get_git_description() + "\n" + self.get_git_stat()



def main():
	config = configparser.ConfigParser()
	config.read(['gitwatcher.cfg', os.path.expanduser('~/.config/LinuxOS.sk/gitwatcher.cfg')])

	watchers = {}
	for section in config.sections():
		options = dict(config.items(section))
		watcher = GitWatcher()
		watcher.directory = options["directory"]
		watcher.icon = options["icon"]
		watcher.project = section
		watcher.watch()
		watchers[section] = watcher

if __name__ == "__main__":
	main()

