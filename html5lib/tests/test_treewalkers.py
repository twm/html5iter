from __future__ import absolute_import, division, unicode_literals

import itertools
import sys

import pytest

try:
    import lxml.etree
except ImportError:
    pass

from .support import treeTypes

from html5lib import html5parser, treewalkers
from html5lib.filters.lint import Filter as Lint

import re
attrlist = re.compile(r"^(\s+)\w+=.*(\n\1\w+=.*)+", re.M)


def sortattrs(x):
    lines = x.group(0).split("\n")
    lines.sort()
    return "\n".join(lines)


def test_all_tokens():
    expected = [
        {'data': {}, 'type': 'StartTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'html'},
        {'data': {}, 'type': 'StartTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'head'},
        {'type': 'EndTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'head'},
        {'data': {}, 'type': 'StartTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'body'},
        {'data': 'a', 'type': 'Characters'},
        {'data': {}, 'type': 'StartTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'div'},
        {'data': 'b', 'type': 'Characters'},
        {'type': 'EndTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'div'},
        {'data': 'c', 'type': 'Characters'},
        {'type': 'EndTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'body'},
        {'type': 'EndTag', 'namespace': 'http://www.w3.org/1999/xhtml', 'name': 'html'}
    ]
    for _, treeCls in treeTypes.items():
        if treeCls is None:
            continue
        p = html5parser.HTMLParser(tree=treeCls["builder"])
        document = p.parse("<html><head></head><body>a<div>b</div>c</body></html>")
        document = treeCls.get("adapter", lambda x: x)(document)
        output = Lint(treeCls["walker"](document))
        for expectedToken, outputToken in zip(expected, output):
            assert expectedToken == outputToken


def set_attribute_on_first_child(docfrag, name, value, treeName):
    """naively sets an attribute on the first child of the document
    fragment passed in"""
    setter = {'ElementTree': lambda d: d[0].set,
              'DOM': lambda d: d.firstChild.setAttribute}
    setter['cElementTree'] = setter['ElementTree']
    try:
        setter.get(treeName, setter['DOM'])(docfrag)(name, value)
    except AttributeError:
        setter['ElementTree'](docfrag)(name, value)


@pytest.mark.parametrize("tree,char", itertools.product(sorted(treeTypes.items()), ["x", "\u1234"]))
def test_fragment_single_char(tree, char):
    expected = [
        {'data': char, 'type': 'Characters'}
    ]

    treeName, treeClass = tree
    if treeClass is None:
        pytest.skip("Treebuilder not loaded")

    parser = html5parser.HTMLParser(tree=treeClass["builder"])
    document = parser.parseFragment(char)
    document = treeClass.get("adapter", lambda x: x)(document)
    output = Lint(treeClass["walker"](document))

    assert list(output) == expected


@pytest.mark.skipif(treeTypes["lxml"] is None, reason="lxml not importable")
def test_lxml_xml():
    expected = [
        {'data': {}, 'name': 'div', 'namespace': None, 'type': 'StartTag'},
        {'data': {}, 'name': 'div', 'namespace': None, 'type': 'StartTag'},
        {'name': 'div', 'namespace': None, 'type': 'EndTag'},
        {'name': 'div', 'namespace': None, 'type': 'EndTag'}
    ]

    lxmltree = lxml.etree.fromstring('<div><div></div></div>')
    walker = treewalkers.getTreeWalker('lxml')
    output = Lint(walker(lxmltree))

    assert list(output) == expected


@pytest.mark.parametrize("treeName",
                         [pytest.param(treeName, marks=[getattr(pytest.mark, treeName),
                                                        pytest.mark.skipif(
                                                            treeName != "lxml" or
                                                            sys.version_info < (3, 7), reason="dict order undef")])
                          for treeName in sorted(treeTypes.keys())])
def test_maintain_attribute_order(treeName):
    treeAPIs = treeTypes[treeName]
    if treeAPIs is None:
        pytest.skip("Treebuilder not loaded")

    # generate loads to maximize the chance a hash-based mutation will occur
    attrs = [(chr(x), str(i)) for i, x in enumerate(range(ord('a'), ord('z')))]
    data = "<span " + " ".join("%s='%s'" % (x, i) for x, i in attrs) + ">"

    parser = html5parser.HTMLParser(tree=treeAPIs["builder"])
    document = parser.parseFragment(data)

    document = treeAPIs.get("adapter", lambda x: x)(document)
    output = list(Lint(treeAPIs["walker"](document)))

    assert len(output) == 2
    assert output[0]['type'] == 'StartTag'
    assert output[1]['type'] == "EndTag"

    attrs_out = output[0]['data']
    assert len(attrs) == len(attrs_out)

    for (in_name, in_value), (out_name, out_value) in zip(attrs, attrs_out.items()):
        assert (None, in_name) == out_name
        assert in_value == out_value


@pytest.mark.parametrize("treeName",
                         [pytest.param(treeName, marks=[getattr(pytest.mark, treeName),
                                                        pytest.mark.skipif(
                                                            treeName != "lxml" or
                                                            sys.version_info < (3, 7), reason="dict order undef")])
                          for treeName in sorted(treeTypes.keys())])
def test_maintain_attribute_order_adjusted(treeName):
    treeAPIs = treeTypes[treeName]
    if treeAPIs is None:
        pytest.skip("Treebuilder not loaded")

    # generate loads to maximize the chance a hash-based mutation will occur
    data = "<svg a=1 refx=2 b=3 xml:lang=4 c=5>"

    parser = html5parser.HTMLParser(tree=treeAPIs["builder"])
    document = parser.parseFragment(data)

    document = treeAPIs.get("adapter", lambda x: x)(document)
    output = list(Lint(treeAPIs["walker"](document)))

    assert len(output) == 2
    assert output[0]['type'] == 'StartTag'
    assert output[1]['type'] == "EndTag"

    attrs_out = output[0]['data']

    assert list(attrs_out.items()) == [((None, 'a'), '1'),
                                       ((None, 'refX'), '2'),
                                       ((None, 'b'), '3'),
                                       (('http://www.w3.org/XML/1998/namespace', 'lang'), '4'),
                                       ((None, 'c'), '5')]
