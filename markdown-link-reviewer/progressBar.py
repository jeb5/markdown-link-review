import sys


class ProgressBar():
	def __init__(self, max, label=""):
		self.max = int(max)
		self.width = len(str(int(max)))
		self.label = label

	def update(self, value, extraText=""):
		paddedPercentage = str(int(value / self.max * 100)).rjust(3, " ")
		paddedValue = str(value).rjust(self.width, " ")
		output = "%s[%s%%][%s of %i] |%s| %s" % (
			self.label, paddedPercentage, paddedValue, self.max, ProgressBar.generateTextBar(value / self.max), extraText)
		sys.stderr.write("\u001b[1G\u001b[2K")  # clears the line, puts cursor at start
		sys.stderr.write(output)
		sys.stderr.flush()

	def finish(self):
		sys.stderr.write("\n")
		sys.stderr.flush()

	def generateTextBar(fullness, maxLength=30, character="█", nonCharacter="░"):
		length = int(fullness * maxLength)
		return (character * length) + (nonCharacter * (maxLength - length))
