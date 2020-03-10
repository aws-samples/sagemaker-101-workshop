# Classifying News Headlines with Keras

## About The Dataset

A dataset of references to news web pages collected from an online aggregator in the period from March 10 to August 10 of 2014. The resources are grouped into clusters that represent pages discussing the same news story. The dataset includes also references to web pages that point (has a link to) one of the news page in the collection.

**Tags:** web pages, news, aggregator, classification, clustering

**License:** Public domain - Due to restrictions on content and use of the news sources, the corpus is limited to web references (urls) to web pages and does not include any text content. The references have been retrieved from the news aggregator through traditional web browsers. 

**File Format:** UTF-8 tab-delimited CSV files

### Data Shape and Statistics

422,937 news pages and divided up into categories:

- "entertainment": 152,746
- "science and technology": 108,465
- "business": 115,920
- "health": 45,615

Clusters:

- 2,076 clusters of similar news for entertainment category
- 1,789 clusters of similar news for science and technology category
- 2,019 clusters of similar news for business category
- 1,347 clusters of similar news for health category

References to web pages containing a link to one news included in the collection are also included. They are represented as pairs of urls corresponding to 2-page browsing sessions. The collection includes 15516 2-page browsing sessions covering 946 distinct clusters divided up into:

6,091 2-page sessions for business category
9,425 2-page sessions for entertainment category

### Content Format

**FILENAME #1:** newsCorpora.csv (102,297,000 bytes)

**DESCRIPTION:** News pages

**FORMAT:** **ID** \t **TITLE** \t **URL** \t **PUBLISHER** \t **CATEGORY** \t **STORY** \t **HOSTNAME** \t **TIMESTAMP**

Where:

- **ID:** Numeric ID
- **TITLE:** News title 
- **URL:** Url
- **PUBLISHER:** Publisher name
- **CATEGORY:** News category (b = business, t = science and technology, e = entertainment, m = health)
- **STORY:** Alphanumeric ID of the cluster that includes news about the same story
- **HOSTNAME:** Url hostname
- **TIMESTAMP:** Approximate time the news was published, as the number of milliseconds since the epoch 00:00:00 GMT, January 1, 1970


**FILENAME #2:** 2pageSessions.csv (3,049,986 bytes)

**DESCRIPTION:** 2-page sessions

**FORMAT:** **STORY** \t **HOSTNAME** \t **CATEGORY** \t **URL**

Where:
- **STORY:** Alphanumeric ID of the cluster that includes news about the same story
- **HOSTNAME:** Url hostname
- **CATEGORY:** News category (b = business, t = science and technology, e = entertainment, m = health)
- **URL:** Two space-delimited urls representing a browsing session
