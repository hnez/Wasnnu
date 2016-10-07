#!/usr/bin/env python3

import sys

import pyrfc3339 as rfc3339
import datetime as dt
import pytz

import crondeltas as cd

weekdays= [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]

def utc_now():
    return(dt.datetime.utcnow().replace(tzinfo=pytz.utc))

def human_readable_timedelta(td):
    td= int(td.total_seconds())

    seconds= td % 60
    minutes= (td//60) % 60
    hours= (td//3600)

    return('{:02}:{:02}:{:02}'.format(hours, minutes, seconds))

class TimeSlice(object):
    def __init__(self, start, end, comment):
        self.start= start
        self.end= end

        self.comment= comment

    @staticmethod
    def from_str(line):
        fields= [a.strip() for a in line.split(' ', 2)]
        fields.extend(None for i in range(len(fields), 3))

        start= rfc3339.parse(fields[0]) if fields[0] else None
        end= rfc3339.parse(fields[1]) if fields[1] else None
        comment= fields[2]

        return (TimeSlice(start, end, comment))

    def is_closed(self):
        return (self.end is not None)

    def fmt_start(self):
        return(rfc3339.generate(self.start) if self.start else '')

    def fmt_end(self):
        return(rfc3339.generate(self.end) if self.end else '')

    def fmt_comment(self):
        return(self.comment.replace('\n', '') if self.comment else '')

    def __lt__(self, other):
        return (self.start < other.start)

    def __repr__(self):
        ret= 'TimeSlice(rfc3339.parse(\'{}\'),rfc3339.parse(\'{}\'), \'{}\')'.format(
            self.fmt_start(),
            self.fmt_end(),
            self.fmt_comment(),
        )

        return (ret)

    def __str__(self):
        ret= '{} {} {}'.format(
            self.fmt_start(),
            self.fmt_end(),
            self.fmt_comment(),
        )

        return (ret.strip())

class TimeTable(object):
    def __init__(self, path):
        self.path=path

        fd= open(path)
        lines= iter(fd)

        self.header= self.parse_header(lines)
        self.slices= self.parse_body(lines)

        fd.close()

    def parse_header(self, lines):
        header={}

        for hdr in lines:
            if not hdr.strip():
                break

            (key, value)= (a.strip() for a in hdr.split(':'))

            if not key in header:
                header[key]=list()

            header[key].append(value)

        return(header)

    def parse_body(self, lines):
        slices=[]

        for slc in lines:
            if slc.startswith('#') or not slc.strip():
                continue

            slices.append(TimeSlice.from_str(slc))

        return(sorted(slices))

    def stamp_in(self):
        if self.slices:
            lastslice= self.slices[-1]

            if not lastslice.is_closed():
                Exception('The last time slice is still open')

        self.slices.append(TimeSlice(utc_now(), None, None))

    def stamp_out(self, comment):
        lastslice= self.slices[-1]

        if lastslice.is_closed():
            Exception('The last time slice is not open')

        lastslice.end=utc_now()
        lastslice.comment= comment

    def to_lines(self):
        for key in sorted(self.header):
            for hdrln in self.header[key]:
                yield('{}: {}'.format(key, hdrln))

        yield('')

        lastday= None

        for s in self.slices:
            day= s.start.date()

            if lastday != day:
                lastday= day

                yield('# {} {} {} ({})'.format(
                    day.year, day.month, day.day, weekdays[day.weekday()]))

            yield(str(s))

    def safe(self):
        fd= open(self.path, 'w')

        fd.writelines(s+'\n' for s in self.to_lines())

        fd.close()

    def active_time_between(self, start=None, end=None):
        if not start:
            start= self.slices[0].start

        if not end:
            end= self.slices[-1].end

        between= filter(
            lambda t: t.start >= start and t.end <=end,
            self.slices
        )

        deltas= iter(t.end - t.start for t in between)

        return(sum(deltas, dt.timedelta(0)))

    def __str__(self):
        return ('\n'.join(self.to_lines()))

class CommandLine(object):
    def cmd(self, args):
        tablename= 'timetable'

        if args[0] == '-f':
            tablename= args[1]
            args=args[2:]

        self.tt= TimeTable(tablename)

        fn= getattr(self, 'cmd_' + args[0])

        return(fn(args[1:]))

    def cmd_in(self, args):
        self.tt.stamp_in()

        self.tt.safe()

    def cmd_out(self, args):
        self.tt.stamp_out(' '.join(args))

        self.tt.safe()

    def cmd_total(self, args):
        dt= self.tt.active_time_between()

        hr= human_readable_timedelta(dt)

        print('Total time spent: ' + hr)

    def cmd_fake(self, args):
        ftt= TimeTable('faked')
        zero= dt.datetime.now()

        lists= cd.CronCombinedLists()

        if 'FakeBlackList' in ftt.header:
            for ln in ftt.header['FakeBlackList']:
                lists.append(cd.CronBlackList(ln, zero))

        if 'FakeWhiteList' in ftt.header:
            for ln in ftt.header['FakeWhiteList']:
                lists.append(cd.CronWhiteList(ln, zero))

        for sl in self.tt.slices:
            (fstart, fend)= lists.fit(sl.end-sl.start)

            fsl= TimeSlice(fstart.replace(tzinfo=pytz.utc),
                           fend.replace(tzinfo=pytz.utc),
                           sl.comment)

            ftt.slices.append(fsl)

        ftt.safe()

if __name__ == '__main__':
    cmdline= CommandLine()

    exit(cmdline.cmd(sys.argv[1:]))
