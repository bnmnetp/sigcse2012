#!/usr/local/bin/python3.2
# -*- coding: utf-8 -*-

import postgresql
import codecs

outf = codecs.open('schedule.txt','w','utf-8')
db = postgresql.open("pq://bmiller:grouplens@localhost/sigcse12")

day_q = db.prepare('''select "timeId",extract(hour from "startTime"),extract(minute from "startTime"), event, location from "DayTime" where weekday = $1 order by extract(hour from "startTime"), extract(minute from "startTime")''')

#day = day_q('Thursday')

session_q = db.prepare('''select "sessionId","Room", "sessionTitle"::bytea, type from "Session"  where "timeId" = $1 order by "sessionId";''')

paper_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title"::bytea,"textAbstract"::bytea from "SessionPaper" natural join "Paper" where "sessionId" = $1 order by "sessionId", "deliveryOrder"''')

for day in [day_q(d) for d in ['Wednesday','Thursday','Friday','Saturday']]:
    print("--------------")
    for session in day:
        outf.write("%d:%02d\t%s\t%s\n" % (session[1],session[2],session[3],session[4]))
        slist = session_q(session[0])
        for sess in slist:
            outf.write("%s %s %s\n"%(sess[1],sess[2].decode('utf-8','ignore'),sess[3]))
            if sess[3] == 'Paper':
                plist = paper_q(sess[0])
                for p in plist:
                    try:
                        outf.write(p[3].decode('utf-8','ignore')+'\n')
                        outf.write(p[4].decode('utf-8','ignore')+'\n')#.decode('utf-16','strict'))
                    except:
                        outf.write('UNICODE ERROR\n')
        