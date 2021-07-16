import argparse
import asyncio
import requests
from progressBar import ProgressBar
from brokenUrls import linkTestLoop
import markdown
import os
import links
from refinementInterface import refinementLoop
from utils import MarkdownException, MarkdownProcessingException, BuildWithCacheException


def parseArgs():
	parser = argparse.ArgumentParser()
	parser.add_argument("markdownFile", nargs="?", help="The path to a markdown file to be parsed")
	parser.add_argument("--url", "-u", dest="markdownUrl", type=str, help="The url of a markdown file to be parsed")
	parser.add_argument("--botOnly", "-b", dest="botOnly", action="store_true", help="Skip the manual review of links by a human")
	parser.add_argument("--noCache", "-nc", dest="noCache", action="store_true", help="Don't use cache files from the mlrDirectory")
	parser.add_argument("--mlrDirectory", "-m", dest="mlrDirectory", default="mlrFiles", type=str, help="The path to the directory in which the output csv file, updated markdown file, changelog and the cache file will be generated")
	return parser.parse_args()
	'''
	Running in bot only mode will only result in changes where the bot can supply a replacement url,
	for example when the url permanently redirects, the bot can supply the destination url as a
	possible replacement
	'''


def getMDFileText(args):
	if args.markdownFile:
		with open(args.markdownFile, "r") as mdFile:
			return mdFile.read()
	elif args.markdownUrl:
		res = requests.get(args.markdownUrl)
		return res.text
	else:
		raise MarkdownException("No markdown file specified")


def main():
	args = parseArgs()
	os.makedirs(args.mlrDirectory, exist_ok=True)

	nlinks = None
	try:
		md = getMDFileText(args)
		mdHash = markdown.getHash(md)
		nlinks = markdown.getLinks(md)
		linkCachePath = os.path.join(args.mlrDirectory, "linkCache")
		if not args.noCache and os.path.isfile(linkCachePath):
			cachedLinks = links.getCachedLinks(linkCachePath, mdHash)
			nlinks = links.mergeInLinks(nlinks, cachedLinks)
			# TODO: somehow determine how many links were loaded from cache, and print this information out

		nbsLinks = [link for link in nlinks if not link.bot.seen]
		if len(nbsLinks):
			bar = ProgressBar(len(nbsLinks) - 1, "Finding broken links...")
			asyncio.run(linkTestLoop(nbsLinks, bar))

		if not args.botOnly:
			nhsLinks = [link for link in nlinks if not link.human.seen]
			nhsProblemLinks = [link for link in nhsLinks if link.bot.needHuman]
			if len(nhsProblemLinks):
				bar = ProgressBar(len(nhsProblemLinks) - 1, "Judging problem links...")
				asyncio.run(refinementLoop(nhsProblemLinks, bar))

		if nlinks != None:
			updatedLinks = [link for link in nlinks if link.shouldBeLogged]
			if len(updatedLinks) != 0:
				try:
					linkLog = os.path.join(args.mlrDirectory, "linkLog.txt")
					with open(linkLog, "w") as llFile:
						links.linksToLog(updatedLinks, llFile)
					print("Saved updated links into log file")
				except Exception as e:
					print(f"Error saving updated links to log file: {e}")

	except MarkdownException as e:
		print(f"Getting markdown file failed: {e}")
	except MarkdownProcessingException as e:
		print(f"Error processing markdown: {e}")
	except BuildWithCacheException as e:
		print(f"Error building links list: {e}")
	except KeyboardInterrupt:
		print("\nProgram canceled")
		return 0
	finally:
		if nlinks != None and not args.noCache:
			try:
				linkCache = os.path.join(args.mlrDirectory, "linkCache")
				links.linksToCache(nlinks, linkCache, mdHash)
				print("Saved to cache")
			except Exception as e:
				print(f"Error saving cache back into file: {e}")
# TODO: rather than making the user manually remove links flagged for removal, maybe add option to autoremove the line containing a link, if that line starts with a markdown bullet point


if __name__ == "__main__":
	main()
