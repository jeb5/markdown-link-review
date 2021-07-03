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
	unknownLinks = [link for link in links if not link.isChecked()]

	urlIndex = {link.url: [] for link in unknownLinks}  # by using lists rather than the links themselves, duplicate links are supported
	for link in unknownLinks:
		urlIndex[link.url].append(link)

	i = len(links) - len(unknownLinks)
	async for url, result in linkTestGenerator((url for url in urlIndex.keys())):
		for link in urlIndex[url]:
			pBar.update(i, str(link))
			if type(result) == str:
				link.setProblem(result)
			else:
				link.setProblem()
			i += 1
	pBar.finish()
