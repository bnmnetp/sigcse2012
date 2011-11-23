#!/usr/local/bin/python3.2

import postgresql


db = postgresql.open("pq://bmiller:grouplens@localhost/sigcse12")

day = db.prepare('''select "timeId",extract(hour from "startTime"),extract(minute from "startTime"), event, location from "DayTime" where weekday = $1 order by extract(hour from "startTime"), extract(minute from "startTime")''')

res = day('Thursday')

paper = db.prepare('''select "proposalId","sessionId","sessionTitle","deliveryOrder","title","textAbstract" from "Session" natural join "SessionPaper" natural join "Paper" where "timeId" = $1 order by "sessionId", "deliveryOrder"''')
for session in res:
    print("%d:%d\t%s\t%s" % (session[1],session[2],session[3],session[4]))
    plist = paper(session[0])
    for p in plist:
        try:
            print(p[2],p[4])
            print(p[5])
        except:
            print('unicode error')
        