#!/usr/bin/env python3

import datetime as dt
import itertools as it

class CronTime(object):
    def __init__ (self, line):
        fields= dict(
            zip(
                'minute hour dom month dow year'.split(),
                line.split()
            )
        )

        bounds= {
            'minute' : range(61),
            'hour' : range(24),
            'dom' : range(1,32),
            'month' : range(1,13),
            'dow' : range(7),
            'year' : range(1970, 2100)
        }

        self.rule= dict(
            (k, self.parse_field(fields[k], bounds[k]))
            for k in bounds
        )

    def parse_field(self, field, avail):
        sub_fields= field.split(',')

        items= set()
        for field in sub_fields:
            if field == '*':
                items.update(avail)

            elif '-' in field:
                (start, end) = field.split('-')
                items.update(
                    range(int(start), int(end)+1)
                )

            else:
                items.add(int(field))

        return(sorted(items.intersection(avail)))

    def next_match(self, start):
        tt= dict(
            zip(
                'year month dom hour minute sec dow yday isdst'.split(),
                start.timetuple()
            )
        )

        def noerr_dt(*kargs):
            try:
                return (dt.datetime(*kargs))
            except ValueError:
                return (None)

        # This is super bad for performance
        candidates= iter (
            noerr_dt(year, month, day, hour, minute)
            for year in self.rule['year']
            for month in self.rule['month']
            for day in self.rule['dom']
            for hour in self.rule['hour']
            for minute in self.rule['minute']
        )

        # TODO: check dow
        clean= filter(lambda c: c is not None, candidates)

        after= it.dropwhile(lambda c: c<start, clean)

        return(next(after))

class CronTimeSlice(object):
    def __init__(self, line):
        (start, end)= line.split(' to ')

        self.start= CronTime(start)
        self.end= CronTime(end)

    def after(self, pot):
        end= pot

        while True:
            start= self.start.next_match(end)
            end= self.end.next_match(start)

            yield(start, end)
