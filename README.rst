SIGCSE Symposium Schedule Creation
==================================

A huge fraction of the information needed to generate the schedule is available in the SIGCSE database.  Here's what you need to do in order to get that information out of the database and into a form that you can start to work with.

#.  Get the password and ftp address to download the database from your conference chairperson.

#.  Convert the Access, yes that Access, database to something you can work with.  In my case I downloaded the Access to Postgresql converter from Bullzip.com.  

#.  Install postgresql if you don't already have it installed.  Go to postgresql.org.  There are some very easy one click installers to download there.

#.  Install Python3.x  (python.org)

#.  Install py-postgresql   (use easy_install, or pip) or download and run setup.py install.

Now that the prerequisites are there simply run the ``makeSchedule.py`` script.

If you need to make changes
===========================

I reverse engineered the database for the makeSchedule script.  Things probably won't change too much from year to year, but in case they do here are some notes.
