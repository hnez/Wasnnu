#!/usr/bin/env python3

import datetime as dt
import itertools as it

class CronMatcher(object):
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

class CronTimePeriods(object):
    def __init__(self, line):
        (start, end)= line.split(' to ')

        self.start= CronMatcher(start)
        self.end= CronMatcher(end)

    def matches_inside(self, after):
        starts= iter(self.start.after(after))
        ends= iter(self.end.after(after))

        for start in starts:
            for end in ends:
                if end >= start:
                    yield(start, end)
                    break

    def matches_outside(self, after):
        inside= iter(self.matches_inside(after))
        (last_start, last_end)= next(inside)

        for (cur_start, cur_end) in inside:
            yield(last_end, cur_start)

            (last_start, last_end)= (cur_start, cur_end)

class CronLimitList(object):
    def __init__(self, periodstr, limit, after, inverted=False):
        self.limit= limit
        self.inverted= inverted

        period= CronTimePeriods(periodstr)
        self.matcher= iter(
            period.matches_outside(after) if inverted else period.matches_inside(after)
        )

        self.period_cur= next(self.matcher)
        self.quota_cur= self.limit

    def next_big_enough(self, duration):
        if (self.limit is not None and duration>self.limit):
            return None

        periods= it.chain([self.period_cur], self.matcher)
        quotas= it.chain([self.quota_cur], it.repeat(self.limit))

        for (self.period_cur, self.quota_cur) in zip(periods, quotas):
            (start, end)= self.period_cur

            if self.quota_cur is None: self.quota_cur= end-start

            if duration<=self.quota_cur and duration<=(end-start):
                self.quota_cur-= duration
                self.period_cur= (start + duration, end)

                return (start, end)

    def next_big_enough_iter(self, duration):
        while True:
            yield(self.next_big_enough(duration))

class CronBlackList(CronLimitList):
    def __init__(self, period, after):
        super().__init__(period, dt.timedelta(0), after, True)

class CronWhiteList(CronLimitList):
    def __init__(self, period, after):
        super().__init__(period, None, after, False)

class CronCombinedLists(list):
    def junction(self, pa, pb):
        start= max(pa[0], pb[0])
        end= min(pa[1], pb[1])

        if end>start:
            return (True, (start, end))
        else:
            return (False, (pa[0]-pb[0]).total_seconds())

    def align(self, periods):
        if (len(periods) < 2):
            return (True, periods[0])

        considered= list()
        junction= None

        for i, p in enumerate(periods):
            stat, junction= self.junction(junction if junction else p, p)

            if not stat:
                return (False, considered if junction < 0 else [i])

            considered.append(i)

        return (True, junction)

    def next_big_enough(self, duration):
        iters= list(
            iter(l.next_big_enough_iter(duration)) for l in self
        )

        cur= list(map(next, iters))

        aligned= False
        while not aligned:
            aligned, ahint= self.align(cur)

            if not aligned:
                for i in ahint:
                    cur[i]= next(iters[i])

        return (ahint)

    def fit(self, duration):
        (start, end)= self.next_big_enough(duration)

        return (start, start+duration)
