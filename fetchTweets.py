import json, requests, HTMLParser, sys, shutil, os, time
from bs4 import BeautifulSoup
from BeautifulSoup import BeautifulSoup
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.ext.declarative import declarative_base

reload(sys)

sys.setdefaultencoding('utf-8')

h = HTMLParser.HTMLParser()

Base = declarative_base()

charsToDelete = 0

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

def stripHtmlTags(htmlTxt):
  if htmlTxt is None:
    return None
  else:
    return h.unescape(''.join(BeautifulSoup(htmlTxt).findAll(text=True)))

def printProgress(msg):
  global charsToDelete
  try:
    for i in range(charsToDelete):
      print "\r",
    charsToDelete = len(str(msg))
    print msg,
    sys.stdout.flush()
  except:
    pass

if __name__ == '__main__':

  startTime = time.time()

  if len(sys.argv) < 2:
    print 'Please suppy the handle to pull tweets from.'
    sys.exit()
  else:
    handle = sys.argv[1]
    engine = create_engine('sqlite:///data/' + handle + '.db')
    Session = sessionmaker(bind=engine)
    print 'Fetching tweets for @' + handle

  session = Session()

  if not os.path.exists(os.path.join(os.getcwd(), 'data')):
    os.makedirs(os.path.join(os.getcwd(), 'data'))

  shutil.copy2(os.path.join(os.getcwd(), 'struct.db'), os.path.join(os.path.join(os.getcwd(), 'data'),handle + '.db'))

  numTweets = 0

  lastID = 0

  url = 'https://twitter.com/i/profiles/show/' + handle + '/timeline/with_replies?composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=60000&last_note_ts=0&latent_count=0&since_id=0'

  while True:

    try:
      r = requests.get(url)
      j = json.loads(r.content)
    except Exception,e:
      printProgress('Number of tweets fetched: ' + str(numTweets) + '\n' + str(e))
      # print str(e)
      pass
    else:
      if not j['has_more_items']:
        break

      soup = BeautifulSoup(j['items_html'].decode('utf-8'))

      for tweet in soup.findAll('li', { 'data-item-type': 'tweet' },recursive=False):
        tweetID, tweetTime, tweetText, retweetHandle = 0, 0, "", ""
        if tweet:
          tweetID = lastID = int(tweet['data-item-id'])
          children = tweet.findChildren(recursive=False)
          for child in children:
            try:
              if 'tweet' in child['class'].split():
                numTweets += 1
                printProgress('Number of tweets fetched: ' + str(numTweets))
                retweetHandle = child['data-screen-name'] if child['data-screen-name'] != handle else ""
                for c in child.findAll('div', { 'class': 'content' },recursive=False):
                  if c:
                    gc = c.findChildren(recursive=False)
                    for p in gc:
                      pClasses = p['class'].split()
                      if 'stream-item-header' in pClasses:
                        tweetTime = int(p.find('small', { 'class': 'time' }).find('a').find('span')['data-time'])
                      if 'tweet-text' in pClasses:
                        tweetText = stripHtmlTags(str(p).decode('utf-8'))
                        newTweet = Tweet(tweetID, tweetTime, tweetText, retweetHandle)
                        session.add(newTweet)
                        session.commit()
            except Exception,e:
              print str(e)
              pass
    finally:
      url = 'https://twitter.com/i/profiles/show/' + handle + '/timeline/with_replies?include_available_features=1&include_entities=1&last_note_ts=0&max_id=' + str(lastID - 1)

  printProgress(str(numTweets) + ' tweets fetched for @' + handle + ' in ' + str(time.time() - startTime) + ' seconds.')