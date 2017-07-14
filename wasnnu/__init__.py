# Copyright (c) 2016 Leonard Göhrs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

import pyrfc3339 as rfc3339
import datetime as dt
import pytz

import itertools as it
from uuid import uuid4 as uuid_random

weekdays= [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]

def human_readable_timedelta(td):
    td= int(td.total_seconds())

    seconds= td % 60
    minutes= (td//60) % 60
    hours= (td//3600)

    return('{:02}:{:02}:{:02}'.format(hours, minutes, seconds))

class TimeSlice(object):
    def __init__(self, header, start=None, end=None):
        if (start is None) and ('Start' in header):
            self.start= rfc3339.parse(header['Start'][0])
        else:
            self.start= start

        if (end is None) and ('End' in header):
            self.end= rfc3339.parse(header['End'][0])
        else:
            self.end= end

        self.header= dict()

        for (k,vlist) in header.items():
            for v in vlist:
                self.header_add(k,v)

    def is_closed(self):
        return (self.end is not None)

    def __lt__(self, other):
        return (self.start < other.start)

    def duration(self):
        return(self.end - self.start)

    def header_add(self, k, v):
        if k in ['Start', 'End']:
            return

        if k not in self.header:
            self.header[k]= list()

        self.header[k].append(v)

    def rfc_start(self):
        return(rfc3339.generate(self.start, utc=False))

    def rfc_end(self):
        return(rfc3339.generate(self.end, utc=False))

    def header_lines(self):
        FMT= '{}: {}'

        if self.start is not None:
            yield(FMT.format('Start', self.rfc_start()))

        if self.end is not None:
            yield(FMT.format('End', self.rfc_end()))

        keys= sorted(self.header.keys())

        for k in keys:
            for v in self.header[k]:
                yield(FMT.format(k, v))

        yield('')

class TimeTable(object):
    def __init__(self, file_path, header, slices):
        self.path= file_path
        self.header= header
        self.slices= slices

        if 'TimeZone' in self.header:
            tzname= self.header['TimeZone'][0]

            self.tz= pytz.timezone(tzname)
        else:
            self.tz= pytz.utc

    @classmethod
    def from_file(cls, path):
        fd= open(path)
        segments= iter(cls.parse_segments(fd))

        header= next(segments, dict())
        slices= sorted(map(TimeSlice, segments))

        fd.close()

        return(TimeTable(path, header, slices))

    @classmethod
    def parse_header(cls, lines):
        header={}

        for hdr in lines:
            if not hdr.strip():
                break

            if hdr.startswith('#'):
                continue

            (key, value)= (a.strip() for a in hdr.split(':', 1))

            if not key in header:
                header[key]=list()

            header[key].append(value)

        return(header)

    @classmethod
    def parse_segments(cls, lines):
        next_seg= cls.parse_header(lines)

        while next_seg:
            yield(next_seg)

            next_seg= cls.parse_header(lines)

    def header_lines(self):
        keys= sorted(self.header.keys())

        for k in keys:
            for v in self.header[k]:
                yield('{}: {}'.format(k, v))

        yield('')

    def dt_now(self):
        return(dt.datetime.now(self.tz))

    def stamp_in(self):
        if self.slices:
            lastslice= self.slices[-1]

            if not lastslice.is_closed():
                raise(UserWarning('The last time slice is still open'))

        slice_new= TimeSlice({}, self.dt_now())
        slice_new.header_add('UUID', str(uuid_random()))

        self.slices.append(slice_new)

    def stamp_out(self, comment):
        lastslice= self.slices[-1]

        if lastslice.is_closed():
            raise(UserWarning('The last time slice is not open'))

        lastslice.end= self.dt_now()

        lastslice.header_add('Description', comment)

    def to_lines(self):
        for ln in self.header_lines():
            yield (ln)

        last_date= None

        for s in self.slices:
            date= s.start.date()

            if date != last_date:
                last_date= date

                yield(
                    '# {} {} {} {}'.format(
                        date.year, date.month, date.day, weekdays[date.weekday()]
                    )
                )

            for ln in s.header_lines():
                yield(ln)

    def save(self):
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

        deltas= iter(s.duration() for s in between)

        return(sum(deltas, dt.timedelta(0)))

    def __str__(self):
        return ('\n'.join(self.to_lines()))

class CommandLine(object):
    def cmd(self, args):
        self.tablename= 'timetable'

        if args[0] == '-f':
            self.tablename= args[1]
            args=args[2:]

        fn= getattr(self, 'cmd_' + args[0])

        try:
            return(fn(args[1:]))
        except UserWarning as u:
            sys.stderr.write('Error: {}\n'.format(' '.join(u.args)))

    def get_timezone_hint(self):
        try:
            fd= open('/etc/timezone')

            return(fd.read().strip())

            fd.close()
        except FileNotFoundError:
            pass

        return('UTC')

    def cmd_init(self, args):
        headers= dict()

        tzname_def= self.get_timezone_hint()
        tzname= input('Timezone [{}]: '.format(tzname_def)).strip()

        headers['TimeZone']= [tzname or tzname_def]

        description= input('Description [None]: ').strip()
        if description:
            headers['Description']= [description]

        tt= TimeTable(self.tablename, headers, [])
        tt.save()

    def cmd_in(self, args):
        tt= TimeTable.from_file(self.tablename)

        tt.stamp_in()

        tt.save()

    def cmd_out(self, args):
        tt= TimeTable.from_file(self.tablename)

        tt.stamp_out(' '.join(args))

        tt.save()

    def cmd_total(self, args):
        tt= TimeTable.from_file(self.tablename)

        dt= tt.active_time_between()

        hr= human_readable_timedelta(dt)

        print('Total time spent: ' + hr)

    def cmd_days(self, args):
        tt= TimeTable.from_file(self.tablename)

        def day_slices():
            date= None
            day= list()

            for s in tt.slices:
                if date != s.start.date():
                    date= s.start.date()

                    if day:
                        yield (day)

                    day= list()

                day.append(s)

            if day:
                yield (day)

        month= None
        month_dur= None

        for day in day_slices():
            date= day[0].start.date()
            deltas= iter(s.duration() for s in day)
            duration= sum(deltas, dt.timedelta(0))

            if date.month != month:
                if month_dur:
                    htd= human_readable_timedelta(month_dur)
                    print('month {}: {}\n'.format(month, htd))

                month= date.month
                month_dur= dt.timedelta(0)

            month_dur+= duration

            print('{} {} {} {}: {}'.format(
                date.year, date.month, date.day, weekdays[date.weekday()],
                duration
            ))

        if month_dur:
            htd= human_readable_timedelta(month_dur)
            print('month {}: {}\n'.format(month, htd))

        tot= tt.active_time_between()
        htot= human_readable_timedelta(tot)
        print('Total time spent: ' + htot)


def main():
    cmdline= CommandLine()

    exit(cmdline.cmd(sys.argv[1:]))
