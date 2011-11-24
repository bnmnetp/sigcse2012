-- Using the sigcse database

select * from "Paper" natural join "PaperAuthor" natural join "Author" where accept = 'Accepted' limit 100;

select * from "Session" natural join "SessionPaper" natural join "Paper" order by "sessionId" limit 100;

select * from "DayTime" where weekday = 'Thursday' order by extract(hour from "startTime"), extract(minute from "startTime");


select * from "Session"  where "timeId" = 2060 order by "sessionId";

select * from "SessionPaper" natural join "Paper" where "sessionId" = 6110 order by "sessionId", "deliveryOrder";

select * from "Session" natural join "SessionPaper" natural join "Paper" where "timeId" = 2060 order by "sessionId", "deliveryOrder";


select "proposalId", "textAbstract" from "SessionSpecialSession" natural join "SpecialSession" where "sessionId" = 10


select * from "SpecialSessionLeader" natural join "Leader" where "proposalId" = 2


select * from "SessionWorkshop" natural join "Workshop" order by "sessionId" limit 20;

select "givenName", surname, institution from "WorkshopOrganizer" natural join "Organizer" where "proposalId" = 2 limit 10;