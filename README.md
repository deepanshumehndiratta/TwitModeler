TwitModeler
===========

Analyze top trends of a particular Twitter handle from publicly available data without OAuth.

Dependencies:
-------------

Python 2.7

Mallet (MAchine Learning for LanguagE Toolkit) - http://mallet.cs.umass.edu/

JDK 7

Apache Ant - http://ant.apache.org/

Mercurial

SQLAlchemy (Python)

BeautifulSoup (Python)

Installation:
--------------------

```
# Set executable permissions to install script

chmod +x install.sh

# Run the install script as SUDO user

sudo ./install.sh
```

Running the script:
--------------------

The analysis runtime is usually around ~15 minutes (Depends on available CPU time and Disk I/O rate.)

```
./run.sh <Twitter Handle to analyze> [,<Number of top trends> | Optional arguments]
```

Abstract
--------

Basic profiling of Twitter handles for initial content generation during signup via Twitter OAuth.

References
----------

Real-Time Topic Modeling of Microblogs - http://www.oracle.com/technetwork/articles/java/micro-1925135.html