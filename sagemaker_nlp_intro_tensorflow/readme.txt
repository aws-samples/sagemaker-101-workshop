SUMMARY: Dataset of references (urls) to news web pages

DESCRIPTION: Dataset of references to news web pages collected from an online aggregator in the period from March 10 to August 10 of 2014. The resources are grouped into clusters that represent pages discussing the same news story. The dataset includes also references to web pages that point (has a link to) one of the news page in the collection.

TAGS: web pages, news, aggregator, classification, clustering

LICENSE: Public domain - Due to restrictions on content and use of the news sources, the corpus is limited to web references (urls) to web pages and does not include any text content. The references have been retrieved from the news aggregator through traditional web browsers. 

FILE ENCODING: UTF-8

FORMAT: Tab delimited CSV files. 

DATA SHAPE AND STATS: 422937 news pages and divided up into:

152746 	news of business category
108465 	news of science and technology category
115920 	news of business category
 45615 	news of health category

2076 clusters of similar news for entertainment category
1789 clusters of similar news for science and technology category
2019 clusters of similar news for business category
1347 clusters of similar news for health category

References to web pages containing a link to one news included in the collection are also included. They are represented as pairs of urls corresponding to 2-page browsing sessions. The collection includes 15516 2-page browsing sessions covering 946 distinct clusters divided up into:

6091 2-page sessions for business category
9425 2-page sessions for entertainment category

 

CONTENT
=======

FILENAME #1: newsCorpora.csv (102.297.000 bytes)
DESCRIPTION: News pages
FORMAT: ID \t TITLE \t URL \t PUBLISHER \t CATEGORY \t STORY \t HOSTNAME \t TIMESTAMP

where:
ID		Numeric ID
TITLE		News title 
URL		Url
PUBLISHER	Publisher name
CATEGORY	News category (b = business, t = science and technology, e = entertainment, m = health)
STORY		Alphanumeric ID of the cluster that includes news about the same story
HOSTNAME	Url hostname
TIMESTAMP 	Approximate time the news was published, as the number of milliseconds since the epoch 00:00:00 GMT, January 1, 1970


FILENAME #2: 2pageSessions.csv (3.049.986 bytes)
DESCRIPTION: 2-page sessions
FORMAT: STORY \t HOSTNAME \t CATEGORY \t URL

where:
STORY		Alphanumeric ID of the cluster that includes news about the same story
HOSTNAME	Url hostname
CATEGORY	News category (b = business, t = science and technology, e = entertainment, m = health)
URL		Two space-delimited urls representing a browsing session
