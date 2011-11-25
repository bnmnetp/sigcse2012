#!/usr/local/bin/python3.2
# -*- coding: utf-8 -*-

# Author:  Brad Miller, Luther College
# Date:  November, 2011
# Description:
# Generate as Much of the SIGCSE Schedule from the database as possible.
# License:

import postgresql
from jinja2 import Template
import re

#outf = codecs.open('schedule.txt','w','utf-8')
db = postgresql.open("pq://bmiller:grouplens@localhost/sigcse12")


day_q = db.prepare('''SELECT "timeId",extract(hour from "startTime"),extract(minute from "startTime"), extract(hour from "endTime"), extract(minute from "endTime"), event, location
                      FROM "DayTime"
                      WHERE weekday = $1
                      order by extract(hour from "startTime"), extract(minute from "startTime")''')

session_q = db.prepare('''select "sessionId","Room", "sessionTitle", type, "reviewerId" from "Session"  where "timeId" = $1 order by "sessionId";''')

# Papers
paper_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title","textAbstract" from "SessionPaper" natural join "Paper" where "sessionId" = $1 order by "sessionId", "deliveryOrder"''')

author_q = db.prepare('''select "givenName", surname, institution from "PaperAuthor" natural join "Author" where "proposalId" = $1 ''')

chair_q = db.prepare('''select "givenName", surname, institution from "Reviewer" where "reviewerId" = $1''')

# Panels
panel_q = db.prepare('''select "proposalId", "textAbstract" from "SessionPanel" natural join "Panel" where "sessionId" = $1 ''')
panelist_q = db.prepare('''select "givenName", surname, institution, "primary" from "PanelPanelist" inner join "Panelist" on("contributorId" = "contributorID") where "proposalId" = $1''')

# Special Sessions
specialsess_q = db.prepare('''select "proposalId", "textAbstract" from "SessionSpecialSession" natural join "SpecialSession" where "sessionId" = $1 ''')
special_leader_q = db.prepare('''select "givenName", surname, institution, "primary" from "SpecialSessionLeader" natural join "Leader" where "proposalId" = $1 ''')

# Workshops
workshop_q = db.prepare('''select "proposalId", "textAbstract"  from "SessionWorkshop" natural join "Workshop" where "sessionId" = $1 ''')
workshop_presenter_q = db.prepare('''select "givenName", surname, institution from "WorkshopOrganizer" natural join "Organizer" where "proposalId" = $1 ''')

# Birds of a Feather
bof_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title","textAbstract" from "SessionBof" natural join "BoF" where "sessionId" = $1 ''')
bof_facilitator_q = db.prepare('''select "givenName", surname, institution from "bofFacilitator" natural join "Facilitator" where "proposalId" = $1 ''')

# Posters
poster_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title","textAbstract" from "SessionPoster" natural join "Poster" where "sessionId" = $1 ''')
poster_presenter_q = db.prepare('''select "givenName", surname, institution from "posterPresenter" natural join "Presenter" where "proposalId" = $1 ''')

#
# Using Jinja2 templates to layout the latex tables.  This is the same
# template engine used in Sphinx and Django.
#
# Needs a dictionary with type, title, room, chair, participants and abstract
ss_panel_t = Template('''\\begin{longtable}[l]{@{}p{1in}@{}p{3in}@{}r}
    {\Large\\textbf{ {{type}} }} & 
    {\Large\\textbf{ {{title}} }} & 
    {\Large\\textbf{ {{room}} }} \\\\
% row 2    
    Chair: & 
    {{chair}}  \\\\[0.5em]
% row 3
    Participants: & 
    \multicolumn{2}{@{}l}{\parbox{3.75in}{ {{participants}}  }} \\\\[2em]
% row 4
    \multicolumn{3}{@{}p{5in}}{ {{abstract}} }
\end{longtable}''')

session_t = Template('''\\begin{longtable}[l]{@{}p{1in}@{}p{3in}@{}r}
    {\Large\\textbf{ {{type}} }} & 
    {\Large\\textbf{ {{title}} }} & 
    {\Large\\textbf{ {{room}} }} \\\\
\\end{longtable}    
''')


def latex_escape(s):
    news = s.replace('&','\\&')
    news = news.replace('#','\\#')
    pat = re.compile(r'(<a.*?>)|</a>')
    news = pat.sub('',news)
    return news.strip()
    
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
            elif row[3] == 'SpecialSession':
                self.sessionList.append(SpecialSession(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'Workshop':
                self.sessionList.append(Workshop(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'BOF':
                self.sessionList.append(BoF(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'Poster':
                self.sessionList.append(Poster(row[0],row[1],row[2],row[3],row[4]))
            else:
                self.sessionList.append(Session(row[0],row[1],row[2],row[3],row[4]))

    def printMe(self):
        print('-----------------')
        print('%s, %d:%02d to %d:%02d' % (self.day,self.startHour,self.startMinute,self.endHour,self.endMinute))
        print('-----------------')

        for session in self.sessionList:
            print()
            session.printMe()
            
    def toLatex(self):
        """docstring for toLatex"""
        print('\\noindent')
        print('\\framebox[5in][l]{{\\Large \\textbf{%s,  %d:%02d to %d:%02d}}}' %  (self.day,self.startHour,self.startMinute,self.endHour,self.endMinute))

        for session in self.sessionList:
            session.toLatex()
            print('''\\vspace{0.5em}
\\noindent\\rule{5in}{0.02cm}
\\vspace{0.5em}''')
                    



class Session:
    def __init__(self,sessionid,room,title,sess_type,chairId):
        self.sessionId = sessionid
        self.room = room
        self.title = title
        self.type = sess_type
        self.chairFirst = ''
        self.chairLast = ''
        self.chairInst = ''
        chair = chair_q(chairId)
        if len(chair) > 0:
            self.chairFirst = chair[0][0]
            self.chairLast = chair[0][1]
            self.chairInst = chair[0][2]

    def printMe(self):
        print("%s %s" % (self.type, self.title))
#        print("Chair: %s %s %s" %(self.chairFirst,self.chairLast,self.chairInst))
        print(self.room)

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        """
        c = {}
        c['type'] = self.type
        c['title'] = latex_escape(self.title)
        c['room'] = self.room
        print(session_t.render(c))

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
        print("Chair:  %s %s %s" % (self.chairFirst,self.chairLast,self.chairInst))
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
            if row[3] == 'Yes':
                self.chairFirst = row[0]
                self.chairLast = row[1]
                self.chairInst = row[2]
            else:
                self.panelists.append("%s %s %s" % (row[0],row[1],row[2]))

    def printMe(self):
        super().printMe()
        print("Chair:  %s %s %s" % (self.chairFirst,self.chairLast,self.chairInst))
        
        for p in self.panelists:
            print(p)

        print(self.abstract)

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        Needs: type, title, room, chair, participants and abstract
        """
        c = {}
        c['type'] = 'PANEL'
        c['title'] = latex_escape(self.title)
        c['room'] = self.room
        c['chair'] = "%s %s %s" % (self.chairFirst,self.chairLast,self.chairInst)
        c['participants'] = ";".join(self.panelists)
        c['abstract'] = latex_escape(self.abstract)
        print(ss_panel_t.render(c))


class SpecialSession(Session):
    """docstring for SpecialSession"""
    def __init__(self, sessionid, room, title, sess_type, chairId):
        super().__init__(sessionid, room, title, sess_type, chairId)
        specialinfo = specialsess_q(sessionid)
        self.abstract = specialinfo[0][1]
        self.proposalId = specialinfo[0][0]
        self.leaders = []
        leaders = special_leader_q(self.proposalId)
        for l in leaders:
            if l[3] == 'Yes':
                self.chairFirst = l[0]
                self.chairLast = l[1]
                self.chairInst = l[2]
            else:    
                self.leaders.append("%s %s %s" % (l[0],l[1],l[2]))

    def printMe(self):
        super().printMe()

        print("Chair:  %s %s %s" % (self.chairFirst,self.chairLast,self.chairInst))
        
        for l in self.leaders:
            print(l)

        print(self.abstract)

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        Needs: type, title, room, chair, participants and abstract
        """
        c = {}
        c['type'] = 'PANEL'
        c['title'] = latex_escape(self.title)
        c['room'] = self.room
        c['chair'] = "%s %s %s" % (self.chairFirst,self.chairLast,self.chairInst)
        c['participants'] = ";".join(self.leaders)
        c['abstract'] = latex_escape(self.abstract)
        print(ss_panel_t.render(c))


        
class Workshop(Session):
    """docstring for Worskshop"""
    def __init__(self, sessionid, room, title, sess_type, chairId):
        super().__init__(sessionid, room, title, sess_type, chairId)
        workshopinfo = workshop_q(sessionid)
        self.abstract = ''
        
        if len(workshopinfo) > 0:
            self.abstract = workshopinfo[0][1]
            self.proposalId = workshopinfo[0][0]
        else:
            print ("*********** ERROR: no info for workshop session %d ", sessionid)
        
        presenters = workshop_presenter_q(self.proposalId)
        self.presenters = []
        for l in presenters:
            self.presenters.append("%s %s %s" % (l[0],l[1],l[2]))
            
    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        for p in self.presenters:
            print(p)
        
        print(self.abstract)

class BoF(Session):
    """docstring for BoF"""
    def __init__(self, sessionid,room,title,sess_type,chairId):
        super().__init__(sessionid,room,title,sess_type,chairId)
        bofinfo = bof_q(sessionid)
        self.abstract = ''
        if len(bofinfo) > 0:
            self.abstract = bofinfo[0][4]
            self.bofTitle = bofinfo[0][3]            
            self.proposalId = bofinfo[0][0]
        else:
            print ("*********** ERROR: no info for workshop session %d ", sessionid)
        
        facilitators = bof_facilitator_q(self.proposalId)
        self.facilitators = []
        for l in facilitators:
            self.facilitators.append("%s %s %s" % (l[0],l[1],l[2]))

    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        print(self.bofTitle)
        
        for p in self.facilitators:
            print(p)

        print(self.abstract)

class Poster(Session):
    """docstring for BoF"""
    def __init__(self, sessionid,room,title,sess_type,chairId):
        super().__init__(sessionid,room,title,sess_type,chairId)
        posterinfo = poster_q(sessionid)
        self.abstract = ''
        if len(posterinfo) > 0:
            self.abstract = posterinfo[0][4]
            self.posterTitle = posterinfo[0][3]            
            self.proposalId = posterinfo[0][0]
        else:
            print ("*********** ERROR: no info for Poster session %d ", sessionid)
        
        facilitators = poster_presenter_q(self.proposalId)
        self.facilitators = []
        for l in facilitators:
            self.facilitators.append("%s %s %s" % (l[0],l[1],l[2]))

    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        print(self.posterTitle)
        
        for p in self.facilitators:
            print(p)

        print(self.abstract)
        
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
#for dayname in ['Wednesday','Thursday','Friday','Saturday']:
for dayname in ['Thursday']:    
    day = day_q(dayname)
    for row in day:
        ts.append(TimeSlot(row[0],row[1],row[2],row[3],row[4],row[5],row[6],dayname))

for t in ts:
    t.toLatex()

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
        