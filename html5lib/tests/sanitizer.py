from __future__ import absolute_import, division, unicode_literals

import codecs
import json

import pytest

from html5lib import parseFragment, serialize


class SanitizerFile(pytest.File):
    def collect(self):
        with codecs.open(str(self.fspath), "r", encoding="utf-8") as fp:
            tests = json.load(fp)
        for i, test in enumerate(tests):
            yield SanitizerTest.from_parent(self, name=str(i), test=test)


class SanitizerTest(pytest.Item):
    @classmethod
    def from_parent(cls, parent, *, name, test):
        node = super().from_parent(parent, name=name)
        node.obj = lambda: 1  # this is to hack around skipif needing a function!
        node.test = test
        return node

    def runtest(self):
        input = self.test["input"]
        expected = self.test["output"]

        parsed = parseFragment(input)
        serialized = serialize(parsed,
                               sanitize=True,
                               omit_optional_tags=False,
                               use_trailing_solidus=True,
                               space_before_trailing_solidus=False,
                               quote_attr_values="always",
                               quote_char="'",
                               alphabetical_attributes=True)
        errorMsg = "\n".join(["\n\nInput:", input,
                              "\nExpected:", expected,
                              "\nReceived:", serialized])
        assert expected == serialized, errorMsg

    def repr_failure(self, excinfo):
        traceback = excinfo.traceback
        ntraceback = traceback.cut(path=__file__)
        excinfo.traceback = ntraceback.filter()

        return excinfo.getrepr(funcargs=True,
                               showlocals=False,
                               style="short", tbfilter=False)
