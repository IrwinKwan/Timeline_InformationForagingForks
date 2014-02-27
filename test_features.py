#!/usr/bin/python
# -*- coding: UTF-8 -*-
import unittest
from features_and_cues_2sqlitecsv import Feature

class TestFeatureTypeExtraction(unittest.TestCase):

    def setUp(self):
        pass

    def test_split(self):
        p2a = r'"Text: Domain Concept (""Since I\'m interested in the fold"")\nLevel of Abstraction (""started with FoldPainter because … it was more generic"")"'
        p2a = p2a.decode('string_escape')
        a = Feature('')
        codes = {"Text: Domain Concept": r'"Since I\'m interested in the fold"' }

        self.assertEqual(a._split_features(p2a), codes)

if __name__ == '__main__':
    unittest.main()