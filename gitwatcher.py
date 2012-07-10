# -*- coding: utf-8 -*-

import configparser
import os
import pyinotify
import re
from pyinotify import WatchManager, ThreadedNotifier
from subprocess import Popen, PIPE


class GitWatcher(object):
	def __init__(self, options):
		self.directory = options["directory"]
		self.icon = options.get("icon", "")
		self.display_time = options.get("display_time", "3600000")

		self.branch_dir = ["refs", "heads"]
		self.git_command = ["git", "--git-dir", self.directory]

		color_add = options.get("color_add", "#00ff00")
		color_remove = options.get("color_remove", "#ff0000");
		self.stat_re = re.compile("([0-9]* )(\+*)(-*)")
		self.stat_sub = "\\1"+self.wrap_span("\\2", {"color": color_add})+self.wrap_span("\\3", {"color": color_remove})

	def watch(self):
		mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO

		self.__wm = WatchManager()
		self.__wm.add_watch(os.path.join(self.directory, *self.branch_dir), mask, rec = True)

		notifier = ThreadedNotifier(self.__wm, self.process_event)
		notifier.start()
		self.display_notify(self.get_commit_title(), self.get_commit_text())

	def process_event(self, event):
		(name, ext) = os.path.splitext(event.pathname)
		if ext == '.lock':
			return
		self.display_notify(self.get_commit_title(), self.get_commit_text())

	def display_notify(self, title, text):
		icon = []
		if self.icon:
			icon = ["-i", self.icon]
		Popen(["notify-send", "-t", self.display_time, "-a", "git"] + icon + ["-u", "low", title, text])

	def call_git(self, arguments):
		return str(Popen(self.git_command + arguments, stdin=PIPE, stdout=PIPE, stderr=PIPE).stdout.readall(), encoding="utf-8")

	def get_git_author(self):
		return self.call_git(["log", "-1", "--format='%an'"]).strip("\n")

	def get_git_description(self):
		return self.call_git(["log", "-1", "--format=%n<b>%s</b>%n%n%b"])

	def get_git_stat(self):
		stat_out = self.call_git(["diff", "--stat", 'HEAD^', 'HEAD'])
		return self.wrap_span(self.stat_re.sub(self.stat_sub, stat_out), {"font": "monospace"})

	def get_commit_title(self):
		return "Commit from: " + self.get_git_author() + ", project: " + self.project

	def get_commit_text(self):
		return self.get_git_description() + "\n" + self.get_git_stat()

	def wrap_span(self, text, attributes = {}):
		return '<span' + self.render_attributes(attributes) + '>' + text + '</span>'

	def render_attributes(self, attributes):
		if not attributes:
			return ""
		return " " + " ".join(map(lambda a: a[0] + '="' + a[1] + '"', attributes.items()))



def main():
	config = configparser.ConfigParser()
	config.read(['gitwatcher.cfg', os.path.expanduser('~/.config/LinuxOS.sk/gitwatcher.cfg')])

	watchers = {}
	for section in config.sections():
		options = dict(config.items(section))
		watcher = GitWatcher(options)
		watcher.project = section
		watcher.watch()
		watchers[section] = watcher

if __name__ == "__main__":
	main()

