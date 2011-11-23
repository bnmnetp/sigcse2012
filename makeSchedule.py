#!/usr/local/bin/python3.2
# -*- coding: utf-8 -*-

# Author:  Brad Miller, Luther College
# Date:  November, 2011
# Description:
# Generate as Much of the SIGCSE Schedule from the database as possible.
# License:

import postgresql
import codecs

outf = codecs.open('schedule.txt','w','utf-8')
db = postgresql.open("pq://bmiller:grouplens@localhost/sigcse12")


day_q = db.prepare('''select "timeId",extract(hour from "startTime"),extract(minute from "startTime"), event, location from "DayTime" where weekday = $1 order by extract(hour from "startTime"), extract(minute from "startTime")''')

session_q = db.prepare('''select "sessionId","Room", "sessionTitle"::bytea, type from "Session"  where "timeId" = $1 order by "sessionId";''')

paper_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title"::bytea,"textAbstract"::bytea from "SessionPaper" natural join "Paper" where "sessionId" = $1 order by "sessionId", "deliveryOrder"''')

author_q = db.prepare('''select "givenName", surname, institution from "PaperAuthor" natural join "Author" where "proposalId" = $1 ''')


for dayname in ['Wednesday','Thursday','Friday','Saturday']:
    day = day_q(dayname)
    print("-------------- %s --------------\n" %dayname)
    for session in day:
        print("%d:%02d\t%s\t%s\n" % (session[1],session[2],session[3],session[4]))
        slist = session_q(session[0])
        for sess in slist:
            print("%s %s %s\n"%(sess[1],sess[2].decode('utf-8','ignore'),sess[3]))
            if sess[3] == 'Paper':
                plist = paper_q(sess[0])
                for p in plist:
                    try:
                        print(p[3].decode('utf-8','ignore')+'\n')
                        authors = author_q(p[0])
                        for a in authors:
                            print("%s %s %s;" % a)
                        print(p[4].decode('utf-8','ignore')+'\n')#.decode('utf-16','strict'))
                    except:
                        print('UNICODE ERROR\n')
        