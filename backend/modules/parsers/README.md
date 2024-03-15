# Parsers

---

Parsers are used to parse/scan through documents. Primary goal is to chunk them so that they can be indexed in the vectordb.

You can write your own parser by inherting the `BaseParser` class from `parser.py`

Finally, register the parser in `__init__.py`
