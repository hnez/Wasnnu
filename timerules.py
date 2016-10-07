#!/usr/bin/env python3

import pyrfc3339 as rfc3339
import datetime as dt
import pytz

from math import ceil, floor

import itertools as it

class TimeRulePivot(object):
    def __init__(self, next_cb, prev_cb):
        self.next_cb= next_cb
        self.prev_cb= prev_cb

    def __reversed__(self):
        return(TimeRulePivot(prev_cb, next_cb))

    def __iter__(self):
        return(self)

    def __next__(self):
        return(self.next_cb())

class TimeRule(object):
    TIMETUPLE_FIELDS= 'year month dom hour minute second dow doy isdst'
    CRON_STR_SYNTAX= 'minute hour dom month dow year'
    CRON_FIELD_BOUNDS= {
        'minute' : range(60),
        'hour' : range(24),
        'dom' : range(1,32),
        'month' : range(1,13),
        'dow' : range(7),
        'year' : range(1970, 2100)
    }

    def __init__(self, cron_str):
        self.cron= self.parse_cron_str(cron_str)

    def float_indexof(self, seq, val):
        for (i, v) in enumerate(seq):
            if v==val:
                return (i)
            if v>val:
                return (i-0.5)

        return(len(seq) - 0.5)

    def pivot(self, relative_to):
        start= self.parse_timetuple(relative_to)
        field_names= self.CRON_STR_SYNTAX.split()

        indexes= dict(
            (k, self.float_indexof(self.cron[k], start[k])) for k in field_names
        )

        def next_cb():
            nonlocal indexes

            indexes= dict((k, ceil(v)) for (k, v) in indexes.items())

            for (k, v) in indexes.items():
                print(k, self.cron[k][v])

        def prev_cb():
            pass

        return (TimeRulePivot(next_cb, prev_cb))

    def parse_timetuple(self, time):
        field_names= self.TIMETUPLE_FIELDS.split()

        fields= dict(
            zip(field_names,time.timetuple())
        )

        return (fields)

    def parse_cron_field(self, field, field_name):
        bounds= self.CRON_FIELD_BOUNDS[field_name]
        sub_fields= field.split(',')

        if '*' in sub_fields:
            return (bounds)

        numbers= set()

        for field in sub_fields:
            if '-' in field:
                (start, end) = field.split('-')
                numbers.update(range(int(start), int(end)+1))
            else:
                numbers.add(int(field))

        return(sorted(numbers.intersection(bounds)))

    def parse_cron_str(self, cron_str):
        field_names= self.CRON_STR_SYNTAX.split()
        raw_fields= cron_str.split()

        parsed_fields= map(self.parse_cron_field, raw_fields, field_names)

        fields= dict(zip(field_names, parsed_fields))

        return(fields)
