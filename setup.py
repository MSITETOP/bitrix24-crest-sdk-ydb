import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="CRestApp",
    version="1.0.0",
    install_requires=['requests', 'aiohttp', 'ydb'],
    author="Kirill Antropov",
    author_email="ka@msite.com",
    description="CRestApp Bitrix 24 REST API wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MSITETOP/bitrix24-crest-sdk-ydb",
    packages=setuptools.find_packages(),
    keywords='bitrix24 rest api bx24 ydb yandex cloud',
    classifiers=[
        "Development Status :: 5 - Production/Stable",

        'Intended Audience :: Developers',

        'Natural Language :: Russian',
        'Natural Language :: English',

        'Topic :: Software Development :: Libraries :: Python Modules',

        "Programming Language :: Python :: 3",

        "License :: OSI Approved :: MIT License",

        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)