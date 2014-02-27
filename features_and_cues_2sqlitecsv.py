#!/usr/bin/python
# -*- ascii -*-

import os
import traceback
from collections import OrderedDict


class FeatureTypeError(Exception):
    pass

class FeatureType:

    @staticmethod
    def instance(code):
        try:
            return code[code.index('('):code.index(')') + 1]
        except ValueError:
            return code

    @staticmethod
    def feature_type(code):
        feature_type = code.replace('"', '')
        if feature_type[:3] == "IF:":
            feature_type = feature_type[3:].strip()

        try:
            feature_type = feature_type[:feature_type.index('(')]
        except ValueError:
            pass

        return feature_type

class Feature:

    @staticmethod
    def match(line):
        m = line.split("\t")
        try:
            int(m[0].strip())
            float(m[1].strip())
        except ValueError:
            return False

        return True

    def __init__(self, line):
        fields = [
            'Participant',
            'Fork',
            'Retro Time',
            'Coder',
            'Information Type',
            'Information Features - David',
            'Information Features - Irwin',
            'Information Features',
            'Notes',
            'Agree',
            'Disagree',
            'IRR'
            ]
        # self.keys_to_keep = fields # Keep all of the fields.
        line_data = line.split('\t')

        self.record = None
        self.valid = True
        self.record = OrderedDict(zip(fields, line_data))

        self.record['Participant'] = int(self.record['Participant'])
        self.record['Fork'] = float(self.record['Fork'])

        # self.record = self._remove_unused_keys(initial_record)

        try:
            self.record['Information Type'] = self._split_feature_types(self.record['Information Type'])
        except (KeyError, IndexError), e:
            # print "Error at p%s fork %.1f: %s" % (self.record['Participant'], self.record['Fork'], str(e))
            print traceback.print_exc()

        print "%d\t%.1f\t%s" % (self.record['Participant'], self.record['Fork'], self.record['Information Type'])

    def _remove_unused_keys(self, initial_record):
        filtered_record = OrderedDict()

        for k in self.keys_to_keep:
            try:
                filtered_record[k] = initial_record[k]
            except KeyError:
                filtered_record[k] = ''

        return filtered_record

    def _convert_yesno_to_boolean(self, record, key):
        if record[key].lower() == 'y' or record[key] == '1':
            return True
        elif record[key] == '' or record[key].lower() == 'n' or record[key] == '0':
            return False
        else:
            raise CodeError("There's a problem with coding %s not being Y or N for index %s at %s."
                % (key, record['Index'], str(record['Time'])))

    def

    def _split_feature_types(self, feature_string):

        features = feature_string.split("\n")

        feature_types_list = [
            'Position',
            'Proximity',
            'Familiarity',
            'JEdit Source',
            'Method arguments or return type',
            'Size of code',
            'Text: domain concepts',
            'Text: GUI Widgets',
            'Contrasting text among items in the same patch',
            'Text: synonyms',
            'Text: antonyms',
            'Level of abstraction',
            'Comments',
            'File type',
            'Hardcoded numbers in source code',
            'Values of variables during execution',
            'Example of how to do something in source code',
            'Exception',
            'External documentation',
            'Unknown']

        codes = []

        for f in features:
            found = False
            feature_type = FeatureType.feature_type(f)
            instance = FeatureType.instance(f)

            # print "Full text: " + f
            # print "Instance: " + instance
            codes.append(feature_type)

            #for types in feature_types_list:
            #    if self._features_synonyms(feature_type) == types:
            #        codes[types] = instance
            #        found = True
            #        break
            #
            #if found == False:
            #    raise FeatureTypeError("Feature Type not found: %s" % f)

        return codes

    def _features_synonyms(self, candidate_type):
        """Keep track of synonyms, misspellings, and other stuff related to the feature type codings."""

        candidate_type_words = frozenset(candidate_type.split(' '))

        feature_types_list = {
            'Position': ['Position', 'Positional'],
            'Proximity': [],
            'Familiarity': [],
            'JEdit Source': [],
            'Method arguments or return type': [],
            'Size of code': [],
            'Text: domain concepts': ['Text: domain concepts', 'Text about domain concepts'],
            'Text: GUI Widgets': [],
            'Contrasting text among items in the same patch': [],
            'Text: synonyms': [],
            'Text: antonyms': [],
            'Level of abstraction': [],
            'Comments': [],
            'File type': [],
            'Hardcoded numbers in source code': [],
            'Values of variables during execution': [],
            'Example of how to do something in source code': [],
            'Exception': [],
            'External documentation': [],
            'Unknown': []
        }

        for k, v in feature_types_list.iteritems():
            feature_type_words = frozenset(k.split(' '))

            intersection = candidate_type_words & feature_type_words

            print intersection

        return feature_type

    def feature_types_table(self):
        pass

    @property
    def valid(self):
        return self.valid

    def __len__(self):
        return len(self.record)

    def __getitem__(self, key):
        return self.record[key]

    def header(self):
        return ('\t'.join(k for k in self.record.keys()))

    def __str__(self):
        return ('\t'.join(str(v) for v in self.record.values()))

    def tab(self):
        r = self.record
        r['Time'] = "00:%s.%03d" % (str(r['Time'].strftime("%M:%S")), r['Time'].microsecond/1000)
        return ('\t'.join(str(v) for v in r.values()))



class DataLoader:
    DIR = os.path.join("..", "timeline_forks_data", "data")

    @staticmethod
    def build_feature(lines_in_record):
        ce = Feature(lines_in_record)
        if ce.valid:
            return ce
        else:
            raise FeatureTypeError("Invalid record for feature")

    @staticmethod
    def load_features():
        filename = DataLoader.features()
        features_list = []

        lines_in_record = ""

        try:
            with open(filename) as f:
                f.readline() # Read past the first header row

                for line in f:
                    if Feature.match(line):
                        if lines_in_record:
                            features_list.append(DataLoader.build_feature(lines_in_record))

                        lines_in_record = line
                    else:
                        lines_in_record += line

            if lines_in_record:
                features_list.append(DataLoader.build_feature(lines_in_record))

        except Exception, e:
            print ("error of some sort: %s %s", e, line)
            traceback.print_exc()


        return features_list

    @staticmethod
    def features():
        return os.path.join(DataLoader.DIR, "feature_types.txt")

if __name__== "__main__":
    f = DataLoader.load_features()
