from bs4 import BeautifulSoup
from mistune import html as mistuneHtml
from utils import LinkScrapingException


def getMDLinks(mdString):
	try:
		soup = BeautifulSoup(mistuneHtml(mdString), features="html.parser")
		linksTags = soup.find_all("a")
		rawLinks = [(tag["href"], tag.string) for tag in linksTags]
		links = [(text, href) for (href, text) in rawLinks if href.startswith("http") and text != None]
		return links
	except Exception as e:
		raise LinkScrapingException(str(e))


def setMDLinks(mdString, replacementPairs):
	return mdString
