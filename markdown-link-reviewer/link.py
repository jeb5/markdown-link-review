import csv
from utils import BuildWithCacheException
from uuid import uuid4


class Link(object):
	def __init__(self, name: str, href: str, stage: int = 0, problem: str = None, judgment: bool = False, replacement: str = None, note: str = ""):
		self.name = name
		self.url = href
		self.stage = stage  # stage: 0 (unchecked) -> 1 (checked) -> 2 (judged)
		self.problem = problem  # None: no problem,  String: the problem
		self.judgement = judgment  # False: judged invalid, True: judged valid
		self.replacement = replacement  # A replacement url
		self.note = note  # Arbitrary note
		self.id = str(uuid4())

	def judge(self, valid: bool, problem=None, replacement=None, note=None):
		self.stage = 2
		self.judgement = valid
		if problem != None:
			self.problem = problem
		if note != None:
			self.note = note
		if replacement != None:
			self.replacement = replacement

	def getId(self):
		return self.id

	def getUrl(self):
		return self.url

	def setProblem(self, problem=None):
		self.stage = 1
		self.problem = problem

	def setReplacement(self, replacement):
		self.replacement = replacement

	def needsJudgement(self):
		return (self.stage == 1 and self.problem != None)

	def isValid(self):
		return (self.stage == 1 and self.problem == None) or (self.stage == 2 and self.judgement == True)

	def isChecked(self):
		return self.stage > 0

	def toArray(self):
		return [str(x) if x != None else "" for x in [self.name, self.url, self.stage, self.problem, self.judgement, self.replacement, self.note]]

	def toJudgementDict(self):
		return {"id": self.id, "url": self.url, "name": self.name, "problem": self.problem}

	def toChangeString(self):
		if self.problem == None:
			return
		if self.replacement == None:
			return f" Removed \"{self.name}\" ({self.url}) ({self.problem}){f'  ({self.note})' if self.note else ''}"
		return f" Updated \"{self.name}\" ({self.url}) to \"{self.replacement}\" ({self.problem}){f'  ({self.note})' if self.note else ''}"

	def __str__(self):
		return self.name[:30] + " - " + self.url[:50]

	@staticmethod
	def fromArray(array):
		name, url, stage, problem, judgement, replacement, note = [x or None for x in array]
		return Link(name, url, int(stage), problem, bool(judgement), replacement, note)


def buildLinksWCache(links, cacheFile=None):
	# make index of cacheFile contents, then loop through md links, using cache if its there
	try:
		if cacheFile:
			csv_reader = csv.reader(cacheFile, delimiter=',')
			cacheIndex = {"".join(row[0:2]): row for row in csv_reader}
		builtLinks = []
		for name, href in links:
			key = name + href
			if cacheFile and key in cacheIndex:
				builtLinks.append(Link.fromArray(cacheIndex[key]))
			else:
				builtLinks.append(Link(name, href))
		return builtLinks
	except Exception as e:
		raise BuildWithCacheException(str(e))


def linksToCache(links, cacheFile):
	csv_writer = csv.writer(cacheFile)
	for link in links:
		csv_writer.writerow(link.toArray())


def linksToLog(links, llFile):
	output = ""
	for link in links:
		output += link.toChangeString() + "\n"
	llFile.write(output)
