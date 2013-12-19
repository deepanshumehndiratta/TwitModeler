import sys, re, os, subprocess, threading, shutil, logging, time
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.ext.declarative import declarative_base
from collections import OrderedDict
from operator import itemgetter

reload(sys)

sys.setdefaultencoding('utf-8')

def log_uncaught_exceptions(exception_type, exception, tb):
  logging.critical(''.join(traceback.format_tb(tb)))
  logging.critical('{0}: {1}'.format(exception_type, exception))

sys.excepthook = log_uncaught_exceptions

Base = declarative_base()

keywords = {}

class Tweet(Base):
  __tablename__ = 'tweets'

  id = Column(Integer, primary_key=True)
  tweet_id = Column(Integer)
  time = Column(Integer)
  text = Column(Text)
  is_retweet = Column(Integer)
  retweet_handle = Column(Text)

  def __init__(self, tweet_id, time, text, retweet_handle=""):
    self.tweet_id = tweet_id
    self.time = time
    self.text = text
    self.retweet_handle = retweet_handle
    self.is_retweet = 0 if not self.retweet_handle else 1

  def __repr__(self):
    return "<Tweet(%s',%s','%s','%s',%s'>" % (self.tweet_id, self.time,\
     self.text, self.is_retweet, self.retweet_handle)

# Pattern for finding urls
u = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

# Pattern for finding mentions
men = re.compile(r'@(\w+)')

# Pattern for finding hashtags
pat = re.compile(r'#(\w+)')

# Pattern for finding pic.twitter.com type URLs
twitpic = re.compile(r'pic.twitter.com\/(\w+)')

def formatTweet(tweet):

  pics = twitpic.findall(tweet)

  for pic in pics:
    idx = tweet.find(pic) + len(pic)
    tweet = tweet[:idx].replace('pic.twitter.com/' + pic, '') + tweet[idx:]

  urls = u.findall(tweet)

  for url in urls:
    idx = tweet.find(url) + len(url)
    tweet = tweet[:idx].replace(url, '') + tweet[idx:]

  mentions = men.findall(tweet)

  for mention in mentions:
    idx = tweet.find('@' + mention) + len('@' + mention)
    tweet = tweet[:idx].replace('@' + mention, '') + tweet[idx:]

  hashtags = pat.findall(tweet)

  for hashtag in hashtags:

    semiFormattedHashTag = ''
    for i in range(len(hashtag)):

      if hashtag[i].isupper() and (i+1 < len(hashtag) and not hashtag[i+1].isupper()):
        semiFormattedHashTag += "_" + hashtag[i].lower()
      else:
        semiFormattedHashTag += hashtag[i]
    if semiFormattedHashTag[0] == '_':
      semiFormattedHashTag = semiFormattedHashTag[1:]

    formattedHashTagParts = []

    for part in semiFormattedHashTag.split('_'):
      if part:
        formattedHashTagParts.append(part)

    formattedHashTag = ' '.join(formattedHashTagParts)

    idx = tweet.find('#' + hashtag) + len('#' + hashtag)
    tweet = tweet[:idx].replace('#' + hashtag, formattedHashTag) + tweet[idx:]

  return tweet

class Process(threading.Thread):

  def __init__(self, callback, i):
    threading.Thread.__init__(self)
    self.callback = callback
    self.i = i

  def runProcess(self, command):
    try:
      p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate()
      p.kill()
    except:
      pass
    return

  def run(self):

    global keywords

    commands = [
      ['bin/mallet', 'import-dir',
        '--remove-stopwords true',
        '--preserve-case false',
        '--input ' + os.path.join(handle_dir, str(self.i)),
        '--output ' + os.path.join(os.path.join(handle_dir, str(self.i)), 'topic-input.mallet'),
        '--keep-sequence'
      ],
      ['bin/mallet', 'train-topics',
        '--num-iterations 200',
        '--num-top-words 3',
        '--doc-topics-threshold 0.26',
        '--input ' + os.path.join(os.path.join(handle_dir, str(self.i)), 'topic-input.mallet'),
        '--num-topics 2',
        '--output-state ' + os.path.join(os.path.join(handle_dir, str(self.i)), 'output_state.gz'),
        '--output-topic-keys ' + os.path.join(os.path.join(handle_dir, str(self.i)), 'output_topic_keys'),
        '--output-doc-topics ' + os.path.join(os.path.join(handle_dir, str(self.i)), 'output_doc_topics.txt')
      ]
    ]

    for command in commands:
      self.runProcess(command)

    data = None

    if os.access(os.path.join(os.path.join(handle_dir, str(self.i)), 'output_topic_keys'), os.R_OK):
      with open(os.path.join(os.path.join(handle_dir, str(self.i)), 'output_topic_keys')) as fp:
        data = fp.read()

    topics = []

    if data:
      for line in data.split('\n'):
        for t in line.split()[2:]:
          topics.append(t)

    for topic in topics:
      if topic in keywords:
        keywords[topic] += 1
      else:
        keywords[topic] = 1
    self.callback()

class ProcessTweet:
  numConcThreads = 25
  numTweets = 0
  processedTweets = 0
  runningThreads = 0
  keepRunning = True
  printing = False
  __charsToDelete = 0

  def __init__(self, numTweets):
    self.numTweets = numTweets

  def printProgress(self, msg):
    while self.printing:
      pass
    self.printing = True
    try:
      for i in range(self.__charsToDelete):
        print "\r",
      self.__charsToDelete = len(str(msg))
      print msg,
      sys.stdout.flush()
    finally:
      self.printing = False

  def run(self):
    for i in range(self.numConcThreads):
      self.runningThreads += 1
      try:
        Process(self.callback, i).start()
      except:
        pass
    while self.keepRunning:
      pass
    self.printProgress('Processed ' + str(self.processedTweets + self.runningThreads) + ' tweets.')
    return

  def callback(self):
    self.processedTweets += 1
    self.runningThreads -= 1
    self.printProgress('Processed ' + str(self.processedTweets) + ' tweets.')
    if self.processedTweets + self.runningThreads >= self.numTweets:
      self.keepRunning = False
    else:
      self.runningThreads += 1
      try:
        Process(self.callback, self.processedTweets + self.runningThreads).start()
      except:
        pass
    return

if __name__ == '__main__':

  if len(sys.argv) > 1:
    handle = sys.argv[1]
    numTopics = int(sys.argv[2]) if len(sys.argv) > 2 else 20
  else:
    print 'Please specify a valid handle.'
    sys.exit(0)

  print 'Starting pre-processing of tweets. Please wait..'

  startTime = time.time()

  handle_dir = os.path.join(os.path.join(os.getcwd(), 'data'), handle)

  if os.path.exists(handle_dir):
    shutil.rmtree(handle_dir)
  
  os.makedirs(handle_dir)

  engine = create_engine('sqlite:///data/' + handle + '.db')
  Session = sessionmaker(bind=engine)
  session = Session()

  tweets = session.query(Tweet)

  for (i, tweet) in enumerate(tweets):
    
    if not os.path.exists(os.path.join(handle_dir, str(i))):
      os.makedirs(os.path.join(handle_dir, str(i)))

    f = open(os.path.join(os.path.join(handle_dir, str(i)), 'tweet.txt'),'w')

    f.write(formatTweet(tweet.text))

    f.close()

  midTime = time.time()

  print 'Pre-processing complete in ' + str(midTime - startTime) + ' seconds. Beginning Topic Modeling..'

  os.chdir(os.path.join(os.getcwd(), 'mallet'))

  pt = ProcessTweet(tweets.count())
  pt.run()

  keywords = OrderedDict(sorted(keywords.items(), key=itemgetter(1), reverse=True))

  try:
    print 'Top ' + str(numTopics) +' trends:'
    for keyword in keywords.keys()[:numTopics]:
      print keyword
  except:
    pass

  session.close()

  print 'Modeling complete in ' + str(time.time() - midTime) + ' seconds.'