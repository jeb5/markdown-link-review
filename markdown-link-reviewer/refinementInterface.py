from aiohttp import web
import os
import json
from bs4.builder import HTML
from selenium.webdriver.chrome.webdriver import WebDriver
import websockets
import asyncio
import selenium
from webbrowser import open as openLink
from utils import ServerCloseException

WEBDIR = os.path.join(os.path.dirname(__file__), "refinementInterface")
FILE_SERVER_PORT = 8005
WEBSOCKET_PORT = 8006


async def serveHtml():

	def respondWithFile(file):
		def handleReq(req):
			return web.FileResponse(file)
		return handleReq

	app = web.Application()
	app.add_routes([web.view('/', respondWithFile(os.path.join(WEBDIR, "refinementInterface.html")))])
	app.add_routes([web.static('/', WEBDIR)])
	runner = web.AppRunner(app)
	await runner.setup()
	site = web.TCPSite(runner, 'localhost', FILE_SERVER_PORT)
	openLink(f"http://localhost:{FILE_SERVER_PORT}")
	await site.start()


connections = set()


def driverSafeGet(driver, url):
	try:
		return driver.get(url)
	except selenium.common.exceptions.WebDriverException as e:
		pass  # If the browser can't open a link, this shouldn't throw an error.


# they shouldn't have told me about nested methods
def websocketLinkRefiner(links, pbar):
	linkIndex = {link.getId(): link for link in links}
	pendingLinkIds = [link.getId() for link in links]
	driver = selenium.webdriver.Chrome()  # TODO: handle driver being closed
	driverSafeGet(driver, links[0].url)

	async def linkSend(linkId):
		return json.dumps(linkIndex[id].toJudgementDict())

	async def sendGreeting(ws):
		await ws.send(json.dumps({"type": "hello", "data": pendingLinkIds}))

	async def handleMessage(message, ws):
		msgDict = json.loads(message)
		msgType = msgDict["type"]
		msgData = msgDict.get("data")

		if msgType == "startLink":
			link = linkIndex[msgData["id"]]

			resJson = json.dumps({"type": "link", "data": link})
			sends = [ws.send(resJson) for ws in connections]
			pbar.update(len(links) - len(pendingLinkIds), str(link))
			await asyncio.gather(*sends)  # starting a link starts this link for all clients
			driverSafeGet(driver, link.url)  # TODO: make this async - some webpages take forever to load
		elif msgType == "updateLink":
			linkId = msgData["id"]
			link = linkIndex[linkId]
			link.humanJudge(msgData.get("broken"), problem=msgData.get("problem"), urlUpdate=msgData.get("replacementUrl"), nameUpdate=msgData.get("replacementName"), needRemove=msgData.get("needRemove"), note=msgData.get("note"))
			if linkId in pendingLinkIds:
				pendingLinkIds.remove(linkId)
			pbar.update(len(links) - len(pendingLinkIds), str(link))
			await ws.send(json.dumps({"type": "linkUpdated", "data": linkId}))
		elif msgType == "endJudgement":
			# This closes the server (hackily)
			raise ServerCloseException()

	async def wsHandler(ws, path):
		connections.add(ws)
		await sendGreeting(ws)
		try:
			async for message in ws:
				await handleMessage(message, ws)

		finally:
			connections.remove(ws)

	return wsHandler


async def refinementLoop(suspectLinks, pBar):
	htmlServer = asyncio.create_task(serveHtml())
	# open a user's web browser here
	try:
		serve = await websockets.serve(websocketLinkRefiner(suspectLinks, pBar), "localhost", WEBSOCKET_PORT)  # the handler function is called once PER connection
		await serve.wait_closed()
	except ServerCloseException:  # this is surely wrong
		serve.close()
	htmlServer.cancel()
