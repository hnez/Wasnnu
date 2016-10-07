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

    def timetuple_dict(self, pit):
        tt= dict(
            zip(
                'year month dom hour minute sec dow yday isdst'.split(),
                pit.timetuple()
            )
        )

        return (tt)

    def after(self, pit):
        after= self.timetuple_dict(pit)

        def seq_starting_at(seq, at):
            return(it.dropwhile(lambda s: s<at, seq))

        def possible_days():
            years_rem= seq_starting_at(self.rule['year'], after['year'])
            days= it.product(years_rem, self.rule['month'], self.rule['dom'])

            for day in days:
                try:
                    dto= dt.date(day[0], day[1], day[2])
                except ValueError:
                    continue

                if dto<pit.date():
                    continue

                if self.timetuple_dict(dto)['dow'] not in self.rule['dow']:
                    continue

                yield(dto)

        possible_times= iter (
            dt.time(hm[0], hm[1]) for hm in
            it.product(self.rule['hour'], self.rule['minute'])
        )

        possible_datetimes= iter (
            dt.datetime.combine(d[0], d[1]) for d in
            it.product(possible_days(), possible_times)
        )

        datetimes_after= it.dropwhile(lambda d: d<pit, possible_datetimes)

        return(datetimes_after)

class CronTimeSlice(object):
    def __init__(self, line):
        (start, end)= line.split(' to ')

        self.start= CronTime(start)
        self.end= CronTime(end)

    def after(self, pit):
        starts= iter(self.start.after(pit))
        ends= iter(self.end.after(pit))

        for start in starts:
            for end in ends:
                if end >= start:
                    yield(start, end)
                    break
