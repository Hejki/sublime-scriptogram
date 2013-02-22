__author__ = 'hejki'

import sublime, sublime_plugin, subprocess
import urllib, urllib2, threading, json, os
from datetime import datetime

class ScriptogramNewCommand(sublime_plugin.ApplicationCommand):
    """Action for create new file for Scriptogr.am service."""

    def run(self):
        self.view = sublime.active_window().new_file()
        self.edit = self.view.begin_edit()
        self.view.window().show_input_panel("Title:", "", self.title_insert_done, None, self.title_insert_done)

    def title_insert_done(self, title = ""):
        self.insert_text("---\nTitle: " + title + "\nDate: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.view.window().show_input_panel("Tags:", "", self.tags_insert_done, None, self.tags_insert_done)

    def tags_insert_done(self, tags = None):
        if tags != None:
            self.insert_text("\nTags: " + tags)

        self.insert_text("\n---\n\n")
        self.view.end_edit(self.edit)
        self.edit = None
        self.view = None

    def insert_text(self, text):
        self.view.insert(self.edit, self.view.sel()[0].begin(), text)

class ScriptogramUploadCommand(sublime_plugin.TextCommand):
    """Action for upload file to Scriptogr.am service."""

    def run(self, edit):
        file_name = self.view.file_name()
        if file_name == None:
            file_name = datetime.now().strftime("%Y-%m-%d_")
        else:
            file_name = os.path.splitext(os.path.basename(file_name))[0]

        self.view.window().show_input_panel("File name:", file_name, self.run_upload, None, None)

    def run_upload(self, file_name):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        thread = ScriptogramApiCall(file_name, text)
        thread.start()

class ScriptogramApiCall(threading.Thread):
    def __init__(self, file_name, text):
        settings = sublime.load_settings("scriptogram.sublime-settings")
        self.appkey = settings.get("appkey")
        self.userid = settings.get("userid")
        self.file_name = file_name
        self.text = text
        threading.Thread.__init__(self)

    def run(self):
        try:
            data = urllib.urlencode({
                "app_key": self.appkey,
                "user_id": self.userid,
                "name": self.file_name,
                "text": self.text
            })
            request = urllib2.Request("http://scriptogr.am/api/article/post/", data)
            response = urllib2.urlopen(request)

            self.result = json.load(response)
            status = self.result.get("status")

            if status == "failed":
                sublime.error_message(self.result.get("reason"))
            elif status == "success":
                sublime.status_message("Success stored as " + self.result.get("name"))
            return

        except (urllib2.HTTPError) as (e):
            err = "%s: HTTP error %s contacting API" % (__name__, str(e.code))
        except (urllib2.URLError) as (e):
            err = "%s: URL error %s contacting API" % (__name__, str(e.reason))

        sublime.error_message(err)
        self.result = False
