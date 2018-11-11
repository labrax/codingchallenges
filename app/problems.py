
import json


JSON_DIR = 'problems/'
JSON_SECTIONS = "sections.json"
JSON_PROBLEM = "/info.json"


class Sections:
    def __init__(self):
        self.section = dict()
        for i in json.load(open(JSON_DIR + JSON_SECTIONS))['sections']:
            self.section[i['code']] = Section(i['code'], i['name'], i['description'], i['problems'], i['visible'])


class Section:
    def __init__(self, code, name, description, problems, visible):
        self.code = code
        self.name = name
        self.description = description
        self.visible = visible
        self.problems = list()
        for i in problems:
            try:
                p = Problem(i)
                self.problems.append(p)
            except:
                print("Error loading problem {}".format(i))


class Problem:
    def __init__(self, code):
        self.settings = json.load(open(JSON_DIR + code + JSON_PROBLEM))
        self.code = code
        self.name = self.settings['name']
        self.short_description = self.settings['short_description']
        self.content = self.settings['content'].split('\n')
        self.files = self.settings['files']
        self.open_testcases = self.settings['test_cases']['open']
        self.closed_testcases = self.settings['test_cases']['closed']
        self.timelimit = self.settings['timelimit']
        self.submission = self.settings['submission']
        self.judge_line = self.settings['judge']['exec_line']

