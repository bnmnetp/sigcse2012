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


day_q = db.prepare('''SELECT "timeId",extract(hour from "startTime"),extract(minute from "startTime"), extract(hour from "endTime"), extract(minute from "endTime"), event, location
                      FROM "DayTime"
                      WHERE weekday = $1
                      order by extract(hour from "startTime"), extract(minute from "startTime")''')

session_q = db.prepare('''select "sessionId","Room", "sessionTitle"::bytea, type, "reviewerId" from "Session"  where "timeId" = $1 order by "sessionId";''')

paper_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title"::bytea,"textAbstract"::bytea from "SessionPaper" natural join "Paper" where "sessionId" = $1 order by "sessionId", "deliveryOrder"''')

author_q = db.prepare('''select "givenName", surname, institution from "PaperAuthor" natural join "Author" where "proposalId" = $1 ''')

chair_q = db.prepare('''select "givenName", surname, institution from "Reviewer" where "reviewerId" = $1''')

panel_q = db.prepare('''select "proposalId", "textAbstract" from "SessionPanel" natural join "Panel" where "sessionId" = $1 ''')
panelist_q = db.prepare('''select "givenName", surname,institution from "PanelPanelist" inner join "Panelist" on("contributorId" = "contributorID") where "proposalId" = $1''')

class TimeSlot:
    def __init__(self,timeId,startHour,startMinute, endHour,endMinute, event, location, day):
        self.timeId = timeId
        self.startHour = startHour
        self.startMinute = startMinute
        self.endHour = endHour
        self.endMinute = endMinute
        self.event = event
        self.location = location
        self.day = day
        self.sessionList = []

        sl = session_q(timeId)
        for row in sl:
            if row[3] == 'Paper':
                self.sessionList.append(PaperSession(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'Panel':
                self.sessionList.append(PanelSession(row[0],row[1],row[2],row[3],row[4]))
            else:
                self.sessionList.append(Session(row[0],row[1],row[2],row[3],row[4]))

    def printMe(self):
        print('-----------------')
        print('%s, %d:%02d to %d:%02d' % (self.day,self.startHour,self.startMinute,self.endHour,self.endMinute))
        print('-----------------')

        for session in self.sessionList:
            print()
            session.printMe()



class Session:
    def __init__(self,sessionid,room,title,sess_type,chairId):
        self.sessionId = sessionid
        self.room = room
        self.title = title
        self.type = sess_type
        chair = chair_q(chairId)
        if len(chair) > 0:
            self.chairFirst = chair[0][0]
            self.chairLast = chair[0][1]
            self.chairInst = chair[0][2]

    def printMe(self):
        print("%s %s" % (self.type, self.title))
        print(self.room)


class PaperSession(Session):
    def __init__(self,sessionid,room,title,sess_type,chairId):
        super().__init__(sessionid,room,title,sess_type,chairId)
        self.paperList = []

        pl = paper_q(self.sessionId)
        for paper in pl:
            self.paperList.append(Paper(paper[0],paper[3], paper[4],paper[2]))

    def printMe(self):
        #print("%s %s" % (self.type, self.title))
        super().printMe()
        print("%s %s %s" % (self.chairFirst,self.chairLast,self.chairInst))
        for paper in self.paperList:
            paper.printMe()

class PanelSession(Session):
    def __init__(self,sessionid,room,title,sess_type,chairId):
        super().__init__(sessionid,room,title,sess_type,chairId)
        panel = panel_q(sessionid)
        self.abstract = panel[0][1]
        self.panelists = []

        res = panelist_q(panel[0][0])
        for row in res:
            self.panelists.append("%s %s %s" % (row[0],row[1],row[2]))

    def printMe(self):
        super().printMe()
        print(self.abstract)
        for p in self.panelists:
            print(p)

class Paper:
    def __init__(self,proposalId, title,abstract,order):
        self.title = title
        self.abstract = abstract
        self.order = order
        self.proposalId = proposalId
        self.authorList = []

        authors = author_q(proposalId)
        for author in authors:
            self.authorList.append("%s %s %s" % author)

    def printMe(self):
        print(self.title)
        print(self.abstract)
        for author in self.authorList:
            print(author)

ts = []
for dayname in ['Wednesday','Thursday','Friday','Saturday']:
    day = day_q(dayname)
    for row in day:
        ts.append(TimeSlot(row[0],row[1],row[2],row[3],row[4],row[5],row[6],dayname))

for t in ts:
    t.printMe()

#for dayname in ['Wednesday','Thursday','Friday','Saturday']:
#    day = day_q(dayname)
#    print("-------------- %s --------------\n" %dayname)
#    for session in day:
#        print("%d:%02d\t%s\t%s\n" % (session[1],session[2],session[3],session[4]))
#        slist = session_q(session[0])
#        for sess in slist:
#            print("%s %s %s\n"%(sess[1],sess[2].decode('utf-8','ignore'),sess[3]))
#            if sess[3] == 'Paper':
#                plist = paper_q(sess[0])
#                for p in plist:
#                    try:
#                        print(p[3].decode('utf-8','ignore')+'\n')
#                        authors = author_q(p[0])
#                        for a in authors:
#                            print("%s %s %s;" % a)
#                        print(p[4].decode('utf-8','ignore')+'\n')#.decode('utf-16','strict'))
#                    except:
#                        print('UNICODE ERROR\n')
        