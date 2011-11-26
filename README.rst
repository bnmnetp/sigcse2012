SIGCSE Symposium Schedule Creation
==================================

A huge fraction of the information needed to generate the schedule is available in the SIGCSE database.  Here's what you need to do in order to get that information out of the database and into a form that you can start to work with.

#.  Get the password and ftp address to download the database from your conference chairperson.

#.  Convert the Access, yes that Access, database to something you can work with.  In my case I downloaded the Access to Postgresql converter from Bullzip.com.  

#.  Install postgresql if you don't already have it installed.  Go to postgresql.org.  There are some very easy one click installers to download there.

#.  Install Python3.x  (python.org)

#.  Install py-postgresql   (use easy_install, or pip) or download and run setup.py install.

#. Install the Jinja2 template module  (use easy_install)

Now that the prerequisites are there simply run the ``makeSchedule.py`` script.

If you need to make changes
===========================

I reverse engineered the database for the makeSchedule script.  Things probably won't change too much from year to year, but in case they do here are some notes.

You can think of the conference as a collection of time slots.  Each time slot can have several sessions.  Some sessions are really generic, like snack time, or plenary sessions.  Others have lots of information you need to get at.  Here's a list of the session types I've implemented:

* Panel
  * SessionPanel --> Panel --> PanelPanelist --> Panelist
  * The PanelPanelist table has a primary column.  If yes this tells you the organizer of this particular panel

* SpecialSession
  * SessionSpecialSession --> SpecialSession --> SpecialSessionLeader --> Leader
  * SpecialSessionLeader has a primary column which again tells you the organizer of this special session.
  
* Paper
  * This one's a bit different than the others.  Each Paper session has a list of Papers that are presented, including the order of presentation.  The paper session has a chair/moderator.
  * SessionPaper --> Paper
  * PaperAuthor --> Author
  
* BoF
  * SessionBof --> Bof --> BofFacilitator --> Facilitator
  
* Poster
  * SessionPoster --> Poster --> PosterPresenter --> Presenter
  
* Workshop
  * SessionWorkshop --> Workshop --> WorkshopOrganizer --> Organizer

  
TODO
====

* Many of the Session sub classes can be parameterized.  The classes can do their work by simply having the prepared query objects passed to them.  This would reduce the number of lines of code and eliminate lots of redundancy.

* The schedule should use ``\colorbox{black}{\color{white} Thursday}`` to highlight the conference day in the footer. 

* More investigation should be done regarding which fonts to use.  Computer Modern may not be the ultimate font for a conference program.
