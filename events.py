#!/usr/bin/env python

import os
from collections import OrderedDict
from datetime import time, datetime, date


class ForkException(Exception):
    pass


class VideoTime:
    @staticmethod
    def convert_to_timestamp(video_time_stamp):
        (minute, s) = video_time_stamp.split(':')
        (second, millisecond) = s.split('.')

        # Use today's date as a placeholder for creating a datetime object for time subtraction
        return datetime.combine(date.today(), time(0, int(minute), int(second), int(millisecond) * 1000))


class Command:
    def __init__(self, line):

        fields = ['Participant',
            'CommandID',
            'Time',
            'Command',
            'ActiveFile',
            'ASTMethod',
            'EclipseCommand',
            'Find',
            'Replace',
            'DocOffset',
            'LineOfCode']
        line_data = line.rstrip('\n').split('\t', len(fields))
        self.record = OrderedDict(zip(fields, line_data))

        try:
            self.record.pop('Participant', None)
            self.record['CommandID'] = int(self.record['CommandID'])
            self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])
            self.record['DocOffset'] = int(self.record['DocOffset'])
            self.record['LineOfCode'] = self._strip_quotes(self.record['LineOfCode'])
        except ValueError, e:
            print "Exception at index %d: %s" % (self.record['CommandID'], str(e))
            self.record['error'] = True

    def _strip_quotes(self, field):
        return field.rstrip('"').lstrip('"')

    def __len__(self):
        return len(self.record)

    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        self.record[key] = value

    def __contains__(self, key):
        return key in self.record

    def header(self):
        return ('\t'.join(k for k in self.record.keys()))

    def __str__(self):
        return ('\t'.join(str(v) for v in self.record.values()))

    def tab(self):
        # Don't output the Line of Code. Also, strip today's date from the timestamp.
        r = self.record
        r['Time'] = "00:%s.%03d" % (str(r['Time'].strftime("%M:%S")), r['Time'].microsecond/1000)
        return ('\t'.join(str(v) for v in r.values()[0:-1]))

class CodeError(Exception):
    pass


class Fork:
    def __init__(self, index, order, name, goal, success):
        self.index = index
        self.order = order
        self.name = name
        self.goal = goal
        self.success = success

    @property
    def index(self):
        return self.index

    @index.setter
    def index(self, index):
        self._index = int(index)

    @property
    def order(self):
        return self.order

    @order.setter
    def order(self, order):
        self._order = int(order)

    @property
    def name(self):
        return self.name

    @name.setter
    def name(self, name):
        if name == "ERROR":
            raise ForkException("Fork Type field is an error.")
        else:
            self._name = name

    @property
    def success(self):
        return self.success

    @success.setter
    def success(self, success):
        if self._success == 'Unsuccessful':
            self._success = False
        elif self._success == 'Successful':
            self._success = True
        else:
            raise ForkException("Fork Success field isn't 'Successful' or 'Unsuccessful'")

    @property
    def goal(self):
        return self.goal

    @goal.setter
    def goal(self, goal):
        self._goal = goal



class CodedEvent:

    def __init__(self, line):
        # A list of every field in the MergedCoding spreadsheet, left-to-right.
        fields = [
            'Index',
            'Time',
            'Transcription',
            'Foraging',
            'Start', 'End', 'Ongoing', 'Code1', 'Code2', 'Code3',
            'Forks',
            'Fork Description',
            'Retrospective fork',
            'Retrospective fork agreement',
            'Fork Names',
            'Retrospective quote',
            'Fork to Goal',
            'Foraging Success',
            'LearningDoing',
            ]
        self.keys_to_keep = [
            'Index',
            'Time',
            'Foraging',
            'Start',
            'End',
            'Ongoing',
            'Forks',
            'Fork Names',
            'LearningDoing',
            'Fork to Goal',
            'Foraging Success'
            ]
        line_data = line.split('\t')

        self.record = None
        if self._is_coded_row(line_data):
            self.valid = True

            initial_record = OrderedDict(zip(fields, line_data))

            self.record = self._remove_unused_keys(initial_record)

            try:
                self.record['Index'] = int(self.record['Index'])
                self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])
                self.record['Foraging'] = self._convert_yesno_to_boolean(self.record, 'Foraging')
                self.record['Forks'] = self._unpack_fork_attributes(self.record)
                self.record['LearningDoing'] = self.record['LearningDoing'].strip()


            except (KeyError, IndexError), e:
                print "Key or Index Error at index %d: %s" % (self.record['Index'], str(e))
                print self.record

        else:
            self.record = None
            self.valid = False

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

    def _is_coded_row(self, line_data):
        if not line_data[0] or not line_data[1]:
            return False
        else:
            return True

    def _unpack_fork_attributes(self, record):
        """Associate fork data with a fork in thie segment.
        The attributes for a fork are the Fork Type (ex: Verified), Success, and the Goal."""

        fork = []
        if int(record['Forks']) > 0:

            fork_names = [ r.strip() for r in record['Fork Names'].split(',') ]
            fork_goals = [ r.strip() for r in record['Fork to Goal'].split(',') ]
            fork_success = [ r.strip() for r in record['Foraging Success'].split(',') ]

            for i in range(0, len(fork_names)):
                fork.append(Fork(record['Index'], i + 1, fork_names[i], fork_goals[i], fork_success[i]))

        return fork


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


class Feature:
    def __init__(self, line):
        fields = ['Participant',
            'Fork',
            'Retro Time',
            'Fork Success',
            'Position',
            'Proximity',
            'Familiarity',
            'JEdit Source',
            'Method arguments/return type',
            'Size of code',
            'Domain Text',
            'GUI Text',
            'Contrast',
            'Synonyms',
            'Antonyms',
            'Level of Abstraction',
            'Comments',
            'File Type',
            'Hardcoded Numbers',
            'Values of Variables',
            'Examples',
            'Exception',
            'External Doc',
            'Unknown',
            'Patch']
        line_data = line.rstrip('\n').split('\t', len(fields))
        self.record = OrderedDict(zip(fields, line_data))

        try:
            # Round off overlapping forks (ex: 11.1 rounds to 11)
            self.record['Fork'] = int(float(self.record['Fork']))

            features_list = self._copy_feature_types(fields, line_data)
            self.record['FeatureType'] = [k for k, v in features_list.items() if v == 'y']

        except ValueError, e:
            print "ValueError at index %d: %s" % (self.record['CommandID'], str(e))
            self.record['error'] = True

    def _copy_feature_types(self, fields, line_data):
        """This is a cheating method so I can save on program text size."""
        f = fields[4:-1]
        l = line_data[4:-1]
        return OrderedDict(zip(f, l))

    def _strip_quotes(self, field):
        return field.rstrip('"').lstrip('"')

    def __len__(self):
        return len(self.record)

    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        self.record[key] = value

    def __contains__(self, key):
        return key in self.record

    def header(self):
        return ('\t'.join(k for k in self.record.keys()))

    def __str__(self):
        return ('\t'.join(str(v) for v in self.record.values()))

    def tab(self):
        # Don't output the Line of Code. Also, strip today's date from the timestamp.
        r = self.record
        r['Time'] = "00:%s.%03d" % (str(r['Time'].strftime("%M:%S")), r['Time'].microsecond/1000)
        return ('\t'.join(str(v) for v in r.values()[0:-1]))

class DataLoader:
    DIR = os.path.join("..", "timeline_forks_data", "data")

    @staticmethod
    def line_matches_participant(line, p):
        try:
            return int(line[ : line.index('\t') ].strip()) == p
        except:
            return False

    @staticmethod
    def load_feature_types(p):
        filename = DataLoader.feature_types()
        command_list = []
        with open(filename) as f:
            f.readline() # Read past header
            f.readline() # Read past header

            for line in f:
                if DataLoader.line_matches_participant(line, p):
                    c = Feature(line)
                    command_list.append(c)
        return command_list

    @staticmethod
    def load_commands(p):
        filename = DataLoader.commands(p)
        command_list = []
        with open(filename) as f:
            f.readline() # Read past header
            f.readline() # Read past the start timestamp

            for line in f:
                c = Command(line)
                command_list.append(c)
        return command_list

    @staticmethod
    def load_codedevents(p):
        filename = DataLoader.codedevents(p)
        codedevent_list = []
        with open(filename) as f:
            f.readline() # Read past the first header row
            f.readline() # Read past the second header row

            for line in f:
                ce = CodedEvent(line)
                if ce.valid:
                    codedevent_list.append(ce)

        return codedevent_list

    @staticmethod
    def feature_types():
        return os.path.join(DataLoader.DIR, "feature_types_matrix.txt")

    @staticmethod
    def commands(pid):
        return os.path.join(DataLoader.DIR, "p%02d-commands.txt" % (pid))

    @staticmethod
    def codedevents(pid):
        return os.path.join(DataLoader.DIR, "p%02d-coded.txt" % (pid))
