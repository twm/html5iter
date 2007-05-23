#RELEASE remove
if __name__ == '__main__':
  import os, sys
  os.chdir(os.path.split(os.path.abspath(__file__))[0])
  sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
from treebuilders import dom
#END RELEASE

#RELEASE add
#from html5lib import html5parser
#from html5lib.treebuilders import dom
#END RELEASE

import unittest

# tests that aren't autogenerated from text files
class MoreParserTests(unittest.TestCase):

  def test_assertDoctypeCloneable(self):
    parser = html5parser.HTMLParser(tree=dom.TreeBuilder)
    doc = parser.parse('<!DOCTYPE HTML>')
    self.assert_(doc.cloneNode(True))

def buildTestSuite():
  return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == '__main__':
    main()