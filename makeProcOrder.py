#!/usr/local/bin/python3.2
# -*- coding: utf-8 -*-

# Author:  Brad Miller, Luther College
# Date:  November, 2011
# Description:
# Generate as Much of the SIGCSE Schedule from the database as possible.
# Copyright (c) 2011 Brad Miller
#
# The MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import postgresql
from jinja2 import Template
import re
from collections import OrderedDict

#outf = codecs.open('schedule.txt','w','utf-8')
db = postgresql.open("pq://bmiller:grouplens@localhost/sigcse2012")


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
workshop_q = db.prepare('''select "proposalId", "textAbstract", "deliveryOrder", "title"  from "SessionWorkshop" natural join "Workshop" where "sessionId" = $1 ''')
workshop_presenter_q = db.prepare('''select "givenName", surname, institution from "WorkshopOrganizer" natural join "Organizer" where "proposalId" = $1 ''')

# Birds of a Feather
bof_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title","textAbstract" from "SessionBof" natural join "BoF" where "sessionId" = $1 ''')
bof_facilitator_q = db.prepare('''select "givenName", surname, institution, "primary" from "bofFacilitator" natural join "Facilitator" where "proposalId" = $1 ''')

# Posters
poster_q = db.prepare('''select "proposalId","sessionId","deliveryOrder","title","textAbstract" from "SessionPoster" natural join "Poster" where "sessionId" = $1 ''')
poster_presenter_q = db.prepare('''select "givenName", surname, institution, "primary" from "posterPresenter" natural join "Presenter" where "proposalId" = $1 ''')

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

paper_head_t = Template('''\\begin{longtable}{@{}p{1in}@{}p{3in}@{}r}
   {\\Large\\textbf{ {{type}} }} &
   {\\Large\\textbf{ {{title}} }} & 
   {\\Large\\textbf{ {{room}}  }} \\\\
%row 2
   Chair:  & 
   {{chair}} & \\\\ \\\\
''')

paper_t = Template('''
{{time}} & 
\\multicolumn{2}{@{}p{3.75in}}{\\large\\textbf{ {{title}} }} \\\\
& \\multicolumn{2}{@{}p{3.75in}}{ {{author}} } \\\\ \\\\
\\multicolumn{3}{@{}p{5in}}{ {{abstract}} } \\\\ \\\\
''')

sheridanf = open('sheridanID2Title.csv','r')
sheridan = {}
for line in sheridanf:
    shid,title = line.split('|')
    title = title.strip()
    if title in sheridan:
        print('duplicate title for: ', title)
    sheridan[title] = shid

def latex_escape(s):
    news = s.replace('&','\\&')
    news = news.replace('#','\\#')
    news = news.replace('$','\\$')
    news = news.replace('%','\%')
    pat = re.compile(r'(<a.*?>)|</a>')
    news = pat.sub('',news)
    return news.strip()

sessionNum = 0
    
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
                self.sessionList.append(PaperSession(row[0],row[1],row[2],row[3],row[4],startHour,startMinute))
            elif row[3] == 'Panel':
                self.sessionList.append(PanelSession(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'SpecialSession':
                self.sessionList.append(SpecialSession(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'Workshop':
                self.sessionList.append(Workshop(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'BOF':
                self.sessionList.append(BoF(row[0],row[1],row[2],row[3],row[4]))
            elif row[3] == 'Poster':
                self.sessionList.append(PosterSession(row[0],row[1],row[2],row[3],row[4]))
            else:
                self.sessionList.append(Session(row[0],row[1],row[2],row[3],row[4]))

    def printMe(self):
        print('-----------------')
        print('%s, %d:%02d to %d:%02d' % (self.day,self.startHour,self.startMinute,self.endHour,self.endMinute))
        print('-----------------')

        for session in self.sessionList:
            print()
            session.printMe()

    def printSummary(self):
        global sessionNum
        print('-----------------')
        print('%s, %d:%02d to %d:%02d' % (self.day,self.startHour,self.startMinute,self.endHour,self.endMinute))
        print('-----------------')

        for session in self.sessionList:
            if session.type in ['Panel','SpecialSession','Paper']:
                print()
                if session.type != 'Plenary Session':
                    sessionNum += 1
                    print('Session ', sessionNum)
                session.printSummary()
            
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

    def printSummary(self):
        print("%s: %s" % (self.type, self.title))
        print("Session Chair: %s %s (%s)" %(self.chairFirst,self.chairLast,self.chairInst))
        print(sheridan.get(self.title,'XXXXX'), self.title)

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        """
        c = {}
        c['type'] = self.type
        c['title'] = latex_escape(self.title)
        c['room'] = self.room
        res = session_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)

class PaperSession(Session):
    def __init__(self,sessionid,room,title,sess_type,chairId,startHour,startMinute):
        super().__init__(sessionid,room,title,sess_type,chairId)
        print('DEBUG: ', chairId)
        self.paperList = []

        pl = paper_q(self.sessionId)
        for paper in pl:
            self.paperList.append(Paper(paper[0],paper[3], paper[4],paper[2],startHour,startMinute))

    def printMe(self):
        #print("%s %s" % (self.type, self.title))
        super().printMe()
        print("Chair:  %s %s %s" % (self.chairFirst,self.chairLast,self.chairInst))
        for paper in self.paperList:
            paper.printMe()

    def printSummary(self):
        print("%s: %s" % (self.type, self.title))
        print("Session Chair: %s %s (%s)" %(self.chairFirst,self.chairLast,self.chairInst))

        for paper in self.paperList:
            print(sheridan.get(paper.title,'XXXXX'), paper.title)
            
    def toLatex(self):
        """docstring for toLatex"""
        res = ""
        c = {}
        c['title'] = latex_escape(self.title)
        c['type'] = 'PAPER'
        c['room'] = self.room
        c['chair'] = "%s %s %s" % (self.chairFirst,self.chairLast,self.chairInst)
        res = paper_head_t.render(c)
        for paper in self.paperList:
            res = res + paper.toLatex()
            
        res += '\n\\end{longtable}\n\n'
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)
        

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
        c['participants'] = "; ".join(self.panelists)
        c['abstract'] = latex_escape(self.abstract)
        res = ss_panel_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)


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
        c['participants'] = "; ".join(self.leaders)
        c['abstract'] = latex_escape(self.abstract)
        res = ss_panel_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)


        
class Workshop(Session):
    """docstring for Worskshop"""
    def __init__(self, sessionid, room, title, sess_type, chairId):
        super().__init__(sessionid, room, title, sess_type, chairId)
        workshopinfo = workshop_q(sessionid)
        self.abstract = ''
        
        if len(workshopinfo) > 0:
            self.abstract = workshopinfo[0][1]
            self.proposalId = workshopinfo[0][0]
            self.deliveryOrder = workshopinfo[0][2]
            self.title = workshopinfo[0][3]
        else:
            print ("*********** ERROR: no info for workshop session %d ", sessionid)
        self.title = re.sub('<.*?>','',self.title) # remove yucky html tags
        num, ttl = self.title.split(':',1)
        try:
            rest,number = num.split()
        except:
            print("DEBUG:",num)
        self.deliveryOrder = number
        self.title = ttl.strip()
        presenters = workshop_presenter_q(self.proposalId)
        self.presenters = []
        for l in presenters:
            self.presenters.append((l[0],l[1],l[2]))

        self.instDict = OrderedDict()
        for author in self.presenters:
            if author[2] not in self.instDict:
                self.instDict[author[2]] = []
            self.instDict[author[2]].append("%s %s" % author[:2])

        self.presenters = []
        for i in self.instDict:
            a = ", ".join(self.instDict[i])
            a = rreplace(a,","," and",1) + ", " + "\\textit{"+i+"}"
            self.presenters.append(a)
            
    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        for p in self.presenters:
            print(p)
        
        print(self.abstract)

    def printSummary(self):
        print('Workshop', self.deliveryOrder)
        print(sheridan.get(self.title,'XXXXXX'),self.title)
        print("; ".join(self.presenters))

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
        c['participants'] = "; ".join(self.presenters)
        c['abstract'] = latex_escape(self.abstract)
        res = ss_panel_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)

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
            if l[3] == 'Yes':
                self.chairFirst = l[0]
                self.chairLast = l[1]
                self.chairInst = l[2]
            else:
                self.facilitators.append("%s %s %s" % (l[0],l[1],l[2]))

    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        print(self.bofTitle)
        
        for p in self.facilitators:
            print(p)

        print(self.abstract)

    def printSummary(self):
        print('BoF')

        print(sheridan.get(self.bofTitle,'XXXXXX'),self.bofTitle)
        print('Chair:',self.chairFirst, self.chairLast, self.chairInst)

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        Needs: type, title, room, chair, participants and abstract
        """
        c = {}
        c['type'] = 'BOF'
        c['title'] = latex_escape(self.bofTitle)
        c['room'] = self.room
        c['chair'] = "%s %s %s" % (self.chairFirst,self.chairLast,self.chairInst)
        c['participants'] = "; ".join(self.facilitators)
        c['abstract'] = latex_escape(self.abstract)
        res = ss_panel_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)


class PosterSession(Session):
    """docstring for BoF"""
    def __init__(self, sessionid,room,title,sess_type,chairId):
        super().__init__(sessionid,room,title,sess_type,chairId)
        posters = poster_q(sessionid)

        self.posterList = []
        for p in posters:
            self.posterList.append(Poster(p[0],p[3],p[4],p[2]))        


    def printMe(self):
        """docstring for printMe"""
        super().printMe()
        print(self.posterTitle)
        
        for p in self.facilitators:
            print(p)

        print(self.abstract)

    def printSummary(self):
        print('POSTER')
        for p in self.posterList:
            print(sheridan.get(p.title,'XXXXXX'),p.title)
            print(";".join(p.authorList))
            print()

    def toLatex(self):
        """
        Take Paper session information and create a tabular
        environment in latex
        Needs: type, title, room, chair, participants and abstract
        """
        c = {}
        c['type'] = 'POSTER'
        c['title'] = latex_escape(self.title)
        c['room'] = self.room
        c['chair'] = latex_escape("%s %s \\textit{%s}" % (self.chairFirst,self.chairLast,self.chairInst))
#        c['participants'] = latex_escape("; ".join(self.facilitators))
#        c['abstract'] = latex_escape(self.abstract)
        res = ss_panel_t.render(c)

        res = paper_head_t.render(c)
        for poster in self.posterList:
            res = res + poster.toLatex()
            
        res += '\n\\end{longtable}\n\n'

        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        print(res)        

class Poster:
    def __init__(self,proposalId, title, abstract,order):
        self.title = title
        self.abstract = abstract
        self.order = order
        self.authorList = []

        authors = poster_presenter_q(proposalId);
        self.instDict = OrderedDict()
        for author in authors:
            if author[2] not in self.instDict:
                self.instDict[author[2]] = []
            self.instDict[author[2]].append("%s %s" % author[:2])
#            self.authorList.append("%s %s %s" % author)
        for i in self.instDict:
            a = ", ".join(self.instDict[i])
            a = rreplace(a,","," and",1) + ", " + i

            self.authorList.append(a)

    def toLatex(self):
        self.authorList = []
        for i in self.instDict:
            a = ", ".join(self.instDict[i])
            a = rreplace(a,","," and",1) + ", \\textit{" + i + "}"
            
            self.authorList.append(a)

        c = {}
        c['title'] = latex_escape(self.title)
        c['author'] = latex_escape("; ".join(self.authorList))
        
        res = poster_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        return res

class Paper:
    def __init__(self,proposalId, title,abstract,order,startHour,startMinute):
        self.title = title
        self.abstract = abstract
        self.order = order
        self.proposalId = proposalId
        self.authorList = []
        self.startMinute = (order-1)*25+startMinute
        self.startHour = startHour
        if self.startMinute >= 60:
            self.startMinute = self.startMinute % 60
            self.startHour += 1
            
        authors = author_q(proposalId)
        self.instDict = OrderedDict()
        for author in authors:
            if author[2] not in self.instDict:
                self.instDict[author[2]] = []
            self.instDict[author[2]].append("%s %s" % author[:2])
#            self.authorList.append("%s %s %s" % author)
        for i in self.instDict:
            a = ", ".join(self.instDict[i])
            a = rreplace(a,","," and",1) + ", " + i

            self.authorList.append(a)

    def printMe(self):
        print(self.title)
        print(self.abstract)
        for author in self.authorList:
            print(author)
            
    def toLatex(self):
        self.authorList = []
        for i in self.instDict:
            a = ", ".join(self.instDict[i])
            a = rreplace(a,","," and",1) + ", \\textit{" + i + "}"
            
            self.authorList.append(a)

        c = {}
        c['title'] = latex_escape(self.title)
        c['abstract'] = latex_escape(self.abstract)
        c['author'] = "; ".join(self.authorList)
        c['time'] = '%d:%02d'% (self.startHour, self.startMinute)
        
        res = paper_t.render(c)
        res = res.replace('{ ','{')
        res = res.replace(' }','}')        
        return res

def rreplace(s, old, new, occ):
    li = s.rsplit(old,occ)
    return new.join(li)

ts = []
for dayname in ['Wednesday','Thursday','Friday','Saturday']:
#for dayname in ['Thursday']:    
    day = day_q(dayname)
    for row in day:
        ts.append(TimeSlot(row[0],row[1],row[2],row[3],row[4],row[5],row[6],dayname))

for t in ts:
    #t.toLatex()
    t.printSummary()

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
        