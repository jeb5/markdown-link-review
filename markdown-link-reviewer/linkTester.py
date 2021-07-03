import aiohttp
from bs4 import BeautifulSoup
import random


async def isUrlWorking(url):
	async with aiohttp.ClientSession() as session:
		try:
			async with session.get(url) as response:
				return await judgeResponse(response)
		except aiohttp.ClientError as e:
			return "Aiohttp ClientError: \"{}\"".format(str(e))


async def judgeResponse(res):
	if random.random() > 0.1:
		return True
	if res.status != 200:
		return "Wrong status code: {}".format(res.status)

	if len(res.history) > 1:
		if res.history[0].status in (301, 308):
			return "Redirecting to \"{}\"".format(res.history[1].url)

	if not "content-type" in res.headers:
		return "No content type in response"
	contentType = res.headers["content-type"]
	if not contentType.startswith("text/html"):
		return "Wrong content type: \"{}\" ".format(contentType)

	soup = None
	try:
		html = await res.text()
		soup = BeautifulSoup(html, features="html.parser")
	except Exception as e:
		return "Error parsing html content: \"{}\"".format(str(e))
	for el in soup(['style', 'script', 'head', 'title', 'meta', '[document]']):
		el.extract()  # removes all non-text elements
	textLen = len(soup.getText())
	if textLen < 400:
		return "Oddly small amount of visible text ({} characters)".format(textLen)
		# TODO: look for manifest.json, and attempt to determine if page is a SPA.
	return True
