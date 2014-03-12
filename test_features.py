#!/usr/bin/python
# -*- coding: UTF-8 -*-
import unittest
from events import *


class TestFeatureTypeExtraction(unittest.TestCase):

    def setUp(self):
        pass

    def test_load_without_fork(self):
        line_without_fork = r'1	11:00.0	: So Im thinking that theres some sort of dependence put on the curly 	0							0		0		No Data				'
        f = CodedEvent(line_without_fork)
        actual = '1\t00:11:00.000\tFalse\t[1\t1\tNo Data\t\tNone]'
        self.assertEquals(f.tab(), actual)

    def test_load_fork(self):
        line_with_fork = r'3	12:00.0	Since there is Im thinking I should look in the textArea because that is where this is happening. But then theres gotta be additional 	1	1			1.start: Since there is Im thinking I should look in the textArea because that is where this is happening.			1	hovers between 2 classes in package explorer	1	y	Verified	David: You decided to start in the FoldPainter.java class after looking at both ShapeFoldPainter.java and SquareFoldPainter.java, did you see those as other choices or what did you see as your other possible choices?	1.start	Successful	L'
        f = CodedEvent(line_with_fork)
        actual = '3\t00:12:00.000\tTrue\t[3\t1\tVerified\t1.start\tsuccessful]'
        self.assertEquals(f.tab(), actual)

    def test_many_forks(self):
        line_with_many_forks = "11	16:00.0	and that is an option in jedit, so theres gotta be a menu associated with it. so we've got jedit menu yay	1	1			6.start:so i'm gonna open i think a couple of these. so i'm gonna open directory provider and try and find delete lines.			1,-1	Considers multiple classes in package explorer	1,-1	y,y	Verified,Removed	David: Okay, I'm going to pause. So, you're looking for something related to the menu and you chose to open up the menu package and then you went to DirertoryProvider.java, did you, what did you see as your other possible choices?	6.start,6.start	Unsuccessful,Unsuccessful	L/L"
        f = CodedEvent(line_with_many_forks)
        actual = '11\t00:16:00.000\tTrue\t[11\t1\tVerified\t6.start\tunsuccessful, 11\t2\tRemoved\t6.start\tunsuccessful]'
        self.assertEquals(f.tab(), actual)

    def test_forks_from_data(self):
        p2 = DataLoader.load_codedevents(2)

        # Verified and Removed Dual Fork
        forks = [Fork(11, 1, 'Verified', '6.start', 'Unsuccessful'), Fork(11, 2, 'Removed', '6.start', 'Unsuccessful')]
        for i in range(0, len(forks)):
            self.assertEqual(p2[10]['Forks'][i], forks[i])

        # Single Fork
        forks = [Fork(27, 1, 'No', '', '')]
        for i in range(0, len(forks)):
            self.assertEqual(p2[26]['Forks'][i], forks[i])

        # Fork without foraging goal map
        forks = [Fork(34, 1, 'Unverified', 'none', 'NA')]
        for i in range(0, len(forks)):
            self.assertEqual(p2[33]['Forks'][i], forks[i])

    def test_features_matrix(self):
        p2 = DataLoader.load_feature_types(2)

        self.assertEquals(p2[0].tab(), "3	1	00:12:11.000	00:12:33.000	Package Explorer	Domain Text	Level of Abstraction")
        self.assertEquals(p2[1].tab(), "5	1	00:12:33.000	00:13:22.000	Editor: FoldPainter.java	Method arguments/return type	Domain Text	Comments")


if __name__ == '__main__':
    unittest.main()