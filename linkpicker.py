#vim: set fileencoding=utf-8
from BeautifulSoup import *
import re
import mechanize
import urllib2
#variables:
#   #comments, subreddit, title content, img/video/text/link
#cluster by subreddit, but not black/white:stuff in coding could be relveant to stuff in programming etc.
#cluster by word relatedness, floppy disks would be associated with other nerdy words

#ideas
#   comment # can be done per subreddit avg, algotrading will always have less than gaming etc.

USERNAME=""
PASSWORD=""


class Post:
    def __init__(self,amtcomments,subreddit,tit,linktype,liked=None):
        self.com = amtcomments
        self.sub = subreddit
        self.title = tit
        self.lt = linktype
        self.liked = liked


#okay so we have a training set of liked/not liked
#do a random forest/knn of data with comments, subreddit as a # (this would require making a spectrum so that r/nazi was neg(r/jewish)etc
#need system of describing similarity between titles, bayes etc
#linktype is easy i think and can be done as a #

#linktype is dependent with subreddit, b/c i like questions in certain areas, but not in programming or math

likedict = {'total':0}
dislikedict = {'total':0}

def scrapeposts():
    likeurl = 'http://www.reddit.com/user/'+USERNAME+'/liked/'
    dislikeurl = 'http://www.reddit.com/user/'+USERNAME+'/disliked/'
    b = mechanize.Browser()
    b.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    b.set_handle_robots(False)
    b.open('http://www.reddit.com')
    b.select_form(nr=1)
    b['user'] = USERNAME
    b['passwd'] = PASSWORD
    resp = b.submit()


    likedposts = []
    page = b.open(likeurl)
    html = page.read()
    soup = BeautifulSoup(html)
    pots = soup.findAll('div')
    for pot in pots:
        for attr in pot.attrs:
            if attr[0] == 'class':
                if 'thing' in attr[1]:
                    likedposts.append(pot)
    while(True):
        try:
            nextbutton = b.find_link(text_regex = re.compile('next ›'),nr=0)
        except:
            break
        page = b.follow_link(nextbutton)
        html = page.read()
        soup = BeautifulSoup(html)
        pots = soup.findAll('div')
        for pot in pots:
            for attr in pot.attrs:
                if attr[0] == 'class':
                    if 'thing' in attr[1]:
                        likedposts.append(pot)

    #loop thru each liked page

    dislikedposts = []
    page = b.open(dislikeurl)
    html = page.read()
    soup = BeautifulSoup(html)
    pots = soup.findAll('div')
    for pot in pots:
        for attr in pot.attrs:
            if attr[0] == 'class':
                if 'thing' in attr[1]:
                    dislikedposts.append(pot)
    while(True):
        try:
            nextbutton = b.find_link(text_regex = re.compile('next ›'),nr=0)
        except:
            break
        page = b.follow_link(nextbutton)
        html = page.read()
        soup = BeautifulSoup(html)
        pots = soup.findAll('div')
        for pot in pots:
            for attr in pot.attrs:
                if attr[0] == 'class':
                    if 'thing' in attr[1]:
                        dislikedposts.append(pot)
    train = [] 
    for post in likedposts:
        post = str(post)
        ind = post.index('<a class="title loggedin')
        end = post[ind:].index('</a>')
        title = post[ind:(ind+end)]
        start = title.rindex('">')+2
        train.append(Post(0,'whocares',title[start:],'nobody',True))

    for post in dislikedposts:
        post = str(post)
        ind = post.index('<a class="title loggedin')
        end = post[ind:].index('</a>')
        title = post[ind:(ind+end)]
        start = title.rindex('">')+2

        train.append(Post(0,'whocares',title[start:],'nobody',False))

    return train



def trainbayes(trainingdata):
    for post in trainingdata:
        tit = post.title
        tit = tit.replace('?','')
        tit = tit.replace('!','')
        tit = tit.replace(',','')
        tit = tit.replace('.','')
        tit = tit.split()
        if post.liked:
            likedict['total'] += 1
            for word in tit: #this is without pruning common words
                if word in likedict:
                    likedict[word] += 1
                else:
                    likedict[word] = 2
        else:
            dislikedict['total'] += 1
            for word in tit:
                if word in dislikedict:
                    dislikedict[word] += 1
                else:
                    dislikedict[word] = 2


        

#break this into two parts?
#bayes the title
#

def prune(sentence):
    commons = ['i','a','the','an','have','has','me','you','he','she']
    new = []
    for word in sentence:
        if word.lower() not in commons:
            new.append(word)

    return new

def classify(title):
    print 'classifing new post'   
    tit = title.split() #this doesnt handle punctuation well
    P = 1
    for word in prune(tit):
        if word not in likedict and word not in dislikedict :
            pass 
        else:
            if word not in likedict:
                print 'setting',word,'to 1 in likes'
                likedict[word] = 1
            if word not in dislikedict:
                print 'setting',word,'to 1 in DISlikes'
                dislikedict[word] = 1

            probwordgivenliked = float( likedict[word] ) / float( likedict['total'] )
            print probwordgivenliked, 'give liked'
            probword = float( likedict[word] + dislikedict[word] ) / float( likedict['total'] + dislikedict['total'] )

            print probword, 'total prob'
            P *= probwordgivenliked
            P /= probword

            print likedict[word],dislikedict[word],likedict['total'],dislikedict['total']
            print '\n\n'
    
    probliked = float( likedict['total'] ) / float( likedict['total'] + dislikedict['total'] )
    print probliked, 'how many like'
    return P * probliked

#train = scrapeposts()

train = scrapeposts()
#train = [post(18,'programming','I think I found a bug', 'self', liked=False),post(18,'programming','Coffescript sucks', 'link', liked=True)]

trainbayes(train)
def getlink(post):
    post = str(post)
    phrase = '<a class="comments" href="'
    try:
        start = post.index(phrase)
    except:
        phrase = '<a class="comments empty" href="'
        start = post.index(phrase)
    end = post[start:].index('" target')
    link = post[start+len(phrase):(start+end)]
    return link
    


def recommend():
    subreddits = ['algotrading','arduino','artificial','askreddit','askscience','explainlikeimfive','math','netsec','programming','robotics','surfing']
    posts = []
    b = mechanize.Browser()
    b.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    b.set_handle_robots(False)
    b.open('http://www.reddit.com')
    b.select_form(nr=1)
    b['user'] = USERNAME
    b['passwd'] = PASSWORD
    resp = b.submit()
    for sub in subreddits:
        url = 'http://www.reddit.com/r/'+sub
        page = b.open(url)
        html = page.read()
        soup = BeautifulSoup(html)
        pots = soup.findAll('div')
        for pot in pots:
            for attr in pot.attrs:
                if attr[0] == 'class':
                    if 'thing' in attr[1]:
                        posts.append([pot,0])
    
    for posted in posts:
        post = str(posted[0])
        ind = post.index('<a class="title loggedin')
        end = post[ind:].index('</a>')
        title = post[ind:(ind+end)]
        start = title.rindex('">')+2
        title = title[start:]
        title = title.replace('?','')
        title = title.replace('!','')
        title = title.replace(',','')
        title = title.replace('.','')
        posted[1] = classify(title)

    posts = sorted(posts, key=lambda x:x[1],reverse=True)
    for posted in posts[:25]:
        print getlink(posted[0])
        print '\n\n'
        
recommend()


def makecsv(posts):
    pass



