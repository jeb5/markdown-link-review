from typing import Pattern
from yarl import URL
import aiohttp
from bs4 import BeautifulSoup


async def isUrlWorking(url):
	async with aiohttp.ClientSession() as session:
		try:
			async with session.get(url) as response:
				return await judgeResponse(response, url)
		except aiohttp.ClientError as e:
			return f"Aiohttp ClientError: \"{e}\""


def urlCleanPath(url):
	'''Returns a url with a trailing / in the path'''
	rUrl = URL(url)
	return str(rUrl.with_path(rUrl.path.removesuffix("/") + "/"))


async def judgeResponse(res, reqUrl):
	'''
	Judges the response from a request to determine whether or not the url is broken
	If the url works, False will be returned
	If a problem is detected, either...
		a:
			The problem is returned as a string, and human intervention will be required
		or b:
			A problem tuple is returned in the form of (problem, urlReplacement, needHuman)
	'''
	if res.status != 200:
		return f"Bad status code: {res.status}"

	if not "content-type" in res.headers:
		return "No content type in response"
	contentType = res.headers["content-type"]
	if not contentType.startswith("text/html"):
		return f"Bad content type: \"{contentType}\""

	soup = None
	try:
		html = await res.text()
		soup = BeautifulSoup(html, features="html.parser")
	except Exception as e:
		return f"Error parsing html content: \"{e}\""
	for el in soup(['style', 'script', 'head', 'title', 'meta', '[document]']):
		el.extract()  # removes all non-text elements
	textLen = len(soup.getText())
	if textLen < 400:
		return f"Oddly small amount of visible text ({textLen} characters)"
		# TODO: look for manifest.json, and attempt to determine if page is a SPA.

	# This needs to be at the end, because if http->https is not the only problem, others should be addressed first
	if len(res.history) > 1:
		permUrl = None
		endUrl = str(res.history[-1].url)
		for i in range(len(res.history) - 1):
			if res.history[i].status in (301, 303, 308):
				permUrl = str(res.history[i + 1].url)

		cleanedUrl = urlCleanPath(reqUrl)
		cleanedEndUrl = urlCleanPath(endUrl)
		cleanedPermUrl = urlCleanPath(permUrl) if permUrl else ""
		cleanedUrlwScheme = str(URL(cleanedUrl).with_scheme("https"))

		# TODO: add detection for redirects away from "www" subdomain, and either ignore these, or provide a more descriptive error message
		if cleanedEndUrl == cleanedUrl:
			pass
		elif cleanedEndUrl == cleanedUrlwScheme:
			# https upgrades do not require a human attention (needHuman is False)
			return ("Site upgraded to https", endUrl, False)
		elif cleanedPermUrl == cleanedUrlwScheme:
			return ("Site upgraded to https", permUrl, False)
		elif cleanedPermUrl and not cleanedUrl == cleanedPermUrl:
			return (f"Permanently redirecting to \"{permUrl}\"", permUrl)
	return False
