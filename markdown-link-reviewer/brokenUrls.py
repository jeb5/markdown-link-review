import asyncio
from linkTester import isUrlWorking
CONCURRENT_REQUESTS = 15


async def testUrl(semaphore, url):
	await semaphore.acquire()
	result = await isUrlWorking(url)
	semaphore.release()
	return url, result


async def linkTestGenerator(urls):
	semaphor = asyncio.Semaphore(CONCURRENT_REQUESTS)
	tasks = [asyncio.create_task(testUrl(semaphor, url)) for url in urls]
	try:
		for task in asyncio.as_completed(tasks):
			yield await task
	except:
		for task in tasks:
			task.cancel()
		raise


async def linkTestLoop(links, pBar):

	urlIndex = {link.url: [] for link in links}  # Because the bot only considers the URL, links with duplicate URLs can be clumped together
	for link in links:
		urlIndex[link.url].append(link)

	i = 0
	async for url, result in linkTestGenerator((url for url in urlIndex.keys())):
		for link in urlIndex[url]:
			pBar.update(i, str(link))
			i += 1
			if result == False:
				link.botJudge(False)
			elif type(result) == str:
				link.botJudge(True, result)
			elif type(result) == tuple:
				link.botJudge(True, *result)

	pBar.finish()
