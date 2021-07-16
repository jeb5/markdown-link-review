from bs4 import BeautifulSoup
from mistune import html as mistuneHtml
from utils import MarkdownProcessingException
from hashlib import sha1
from links import Link
import re


def getLinks(md):
	'''Takes in a markdown string, and returns a duplicate-removed list of links'''
	try:
		soup = BeautifulSoup(mistuneHtml(md), features="html.parser")
		linksTags = soup.find_all("a")
		rawLinks = [(tag.string, tag["href"]) for tag in linksTags]

		def validLink(link):
			name, url = link
			return name != None and url.startswith("http")
		filteredLinks = [link for link in rawLinks if validLink(link)]  # filters out all empty and relative links

		tupleLinks = []
		linkIndex = {}
		linkLocations = set()
		for name, url in filteredLinks:

			lt = f"[{name}]({url})"
			index = md.find(lt, 0)
			i = 0
			while index in linkLocations:  # find a *new* instance of the link
				index = md.find(lt, index + 1)
				i += 1
			if index == -1:
				print(name)
				raise Exception(f"Cannot find instance {i+1} of link \"{lt}\"")
			linkLocations.add(index)

			if i > 0:
				tupleLinks[linkIndex[lt]] = (name, url, i)
			else:
				linkIndex[lt] = len(tupleLinks)
				tupleLinks.append((name, url, 0))

		return [Link.fromTuple(tl) for tl in tupleLinks]
	except Exception as e:
		raise e
		raise MarkdownProcessingException(str(e))


def getHash(md):
	'''Takes in a string, and returns the sha1 hash'''
	cleanMd = md.encode('utf-8', 'ignore')
	return sha1(cleanMd).hexdigest()
