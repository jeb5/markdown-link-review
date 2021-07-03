from setuptools import setup

setup(name="markdown-link-reviewer",
      version="0.1",
      description="Review and update broken links in markdown files.",
      author="Example name",
      author_email="email@example.com",
      license="MIT",
      packages=["markdown-link-reviewer"],
      install_requires=[
          "aiohttp"
      ],
      zip_safe=False)
