#!/usr/bin/python
# -*- coding: UTF-8 -*-
import unittest
from events import DataLoader
from events import Fork


class TestFeatureTypeExtraction(unittest.TestCase):

    def setUp(self):
        pass

    def test_forks(self):
        p2 = DataLoader.load_codedevents(2)



        self.assertEqual(p2[1]['Forks'], [])

        f = Fork(3, 1, 'Verified', '1.start', 'Successful')
        self.assertEquals(p2[2]['Forks'][0].index, f.index)

        f = Fork(11, 1, 'Verified', '6.start', 'Unsuccessful')
        self.assertEqual(p2[10]['Forks'][0].order, f.order)

        f = Fork(11, 2, 'Verified', '6.start', 'Unsuccessful')
        self.assertEqual(p2[10]['Forks'][1].order, f.order)



if __name__ == '__main__':
    unittest.main()