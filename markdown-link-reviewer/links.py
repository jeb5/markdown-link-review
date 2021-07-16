from utils import BuildWithCacheException, dotdict
from uuid import uuid4
import json


class Link(dotdict):
	'''
	A link in a markdown file consists of some url, and some "name" text.
	Each link object represents a single markdown "link".
	Multiple identical links (same name and link) SHOULD share the same link object 
	Properties:
		name: the "name" text given to the link in markdown (string)
		url: the url given to the link in markdown (string)
		occurances: the number of times this link appears in the markdown (int)
		bot:
			seen: true if the bot has considerd this link (bool)
			broken: true if the bot has judged this link invalid (bool)
			problem: the problem identified by the bot (string or "")
			replacement: the replacement url prescribed by the bot (string or "")
			needHuman: true if the bot wants a second opinion (bool)
		human:
			seen: true if the human has considered this link (bool)
			broken: true if the human has judged this link invalid (bool)
			problem: the problem identified by the human (string or "")
			urlUpdate: the replacement url (string or "")
			nameUpdate: the replacement link name (string or "")
			needRemove: true if link needs to be removed entirely (bool)
			note: any extra human comments (string or "")
	'''

	def __init__(self, data: dict):
		super().__init__()
		bot = data.get("bot", {})
		human = data.get("human", {})
		newData = dotdict({
			"_id": str(uuid4()),
			"url": str(data.get("url")),
			"name": str(data.get("name")),
			"occurrences": int(data.get("occurrences")),
			"bot": dotdict({
				"seen": bool(bot.get("seen", False)),
				"broken": bool(bot.get("broken", False)),
				"problem": str(bot.get("problem", "")),
				"urlUpdate": str(bot.get("urlUpdate", "")),
				"needHuman": bool(bot.get("needHuman", False)),
			}),
			"human": dotdict({
				"seen": bool(human.get("seen", False)),
				"broken": bool(human.get("broken", False)),
				"problem": str(human.get("problem", "")),
				"urlUpdate": str(human.get("urlUpdate", "")),
				"nameUpdate": str(human.get("nameUpdate", "")),
				"needRemove": bool(human.get("needRemove", False)),
				"note": str(human.get("note", "")),
			})
		})
		self.update(newData)

	@property
	def freshProblem(self):
		if self.human.seen:
			return self.human.problem
		if self.bot.seen:
			return self.bot.problem
		return ""

	@property
	def freshUrl(self):
		if self.human.seen and self.human.urlUpdate != "":
			return self.human.urlUpdate
		if self.bot.seen and self.bot.urlUpdate != "":
			return self.bot.urlUpdate
		return self.url

	@property
	def freshName(self):
		if self.human.seen and self.human.nameUpdate != "":
			return self.human.nameUpdate
		return self.name

	@property
	def oldMd(self):
		return f"[{self.name}]({self.url})"

	@property
	def newMd(self):  # should use replacement url and name
		return f"[{self.freshName}]({self.freshUrl})"

	@property
	def hasChanged(self):
		return self.oldMd != self.newMd

	@property
	def shouldBeLogged(self):
		return self.hasChanged or self.human.note != "" or self.human.broken

	def getId(self):
		return self._id

	# def toJson(self):
	# 	return json.dumps({key: value for key, value in self.items() if not key.startswith("_")})  # serialize all non _private fields

	def fingerprint(self):
		return f"{self.name}:{self.url}:{self.occurances}"

	def __str__(self):
		return f"{self.name[:30]}  -  {self.url[:50]}"

	@staticmethod
	def fromTuple(tupleLink):
		'''Creates a link object from a tuple in the form of (name,url,occurrences)'''
		name, url, occurrences = tupleLink
		return Link({"name": name, "url": url, "occurrences": occurrences})

	def botJudge(self, broken: bool, problem: str = "", urlUpdate: str = "", needHuman: bool = True):
		'''Sets bot properties of the link'''
		self.bot.seen = True
		if broken:
			self.bot.broken = broken
			self.bot.problem = problem
			self.bot.urlUpdate = urlUpdate
			self.bot.needHuman = needHuman

	def humanJudge(self, broken: bool, problem: str = "", urlUpdate: str = "", nameUpdate: str = "", needRemove: bool = False, note: str = ""):
		'''Sets human properties of the link'''
		self.human.seen = True
		if note:
			self.human.note = note
		if broken:
			self.human.broken = broken
			self.human.problem = problem
			self.human.urlUpdate = urlUpdate
			self.human.nameUpdate = nameUpdate
			self.human.needRemove = needRemove

	def toChangeString(self):
		noteText = f" Note: {self.human.note}" if self.human.note else ""
		problemText = f": {self.freshProblem}" if self.freshProblem else ""
		if self.human.needRemove:
			return f"Removed \"{self.oldMd}\"{problemText}{noteText}"
		if not self.hasChanged:
			if noteText:
				return noteText
			return
		if self.freshName != self.name and self.freshUrl != self.url:
			return f"Updated \"{self.oldMd}\" to \"{self.newMd}\"{problemText}{noteText}"
		elif self.freshName != self.name:
			return f"Updated name of \"{self.oldMd}\" to \"{self.name}\"{problemText}{noteText}"
		elif self.freshUrl != self.url:
			return f"Updated url of \"{self.oldMd}\" to \"{self.freshUrl}\"{problemText}{noteText}"


'''
class oldlink(object):
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
'''


def getCachedLinks(cacheFilePath, markdownHash):
	try:
		with open(cacheFilePath, "r") as cacheFile:
			cacheLines = cacheFile.readlines()
		if len(cacheLines) == 0 or markdownHash == cacheLines[0]:
			return []
		links = [Link(json.loads(line)) for line in cacheLines[1:]]
		return links
	except Exception as e:
		raise BuildWithCacheException(str(e))


def linksToCache(links, cacheFilePath, markdownHash):
	cacheContent = "\n".join([markdownHash, *[json.dumps({key: value for key, value in link.items() if not key.startswith("_")}) for link in links]])
	with open(cacheFilePath, "w") as cacheFile:
		cacheFile.write(cacheContent)


def linksToLog(links, llFile):
	output = "\n".join([link.toChangeString() for link in links])
	llFile.write(output)


def mergeInLinks(links, betterLinks):
	blIndex = {link.fingerprint(): link for link in betterLinks}
	return [blIndex.get(link.fingerprint(), link) for link in links]
