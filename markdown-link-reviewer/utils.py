class MarkdownException(Exception):
	pass


class MarkdownProcessingException(Exception):
	pass


class BuildWithCacheException(Exception):
	pass


class ServerCloseException(Exception):
	pass


class dotdict(dict):
	"""dot.notation access to dictionary attributes"""
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__
