from rake_nltk import Metric, Rake
import nltk
import math
import sentence
from nltk.corpus import stopwords
import pandas as pd

N_SIM_SENTENCES=4 #Default number of cloud sentences to generate

# class mmr_class():

# def __init__(self):
#   # self.gtxt = {}
#   # self.itxt = {}
#   pass

# Function to return lines to calculate the overall length and for input to RAKE

_stop_words = set(stopwords.words('english'))
def keyword_generator(sentences):
  """Expects list of sanitized tokenized sentences"""
  query2 = rakeQuery(sentences)
  my_filter = lambda tple : tple[0].isalnum() and not tple[0].isdigit() and len(tple[0]) > 3 and tple[0] not in _stop_words
  sorted_pairs = [tple for tple in filter(my_filter, query2.most_common(len(query2)))]
  return sorted_pairs

sanitizer = {"\n": " ", "''": "\"", "``":"\"", " +":" "}
def sanitize(sent):
  """Not complete sanitization method, but it's the one they were using"""
  for dirty, clean in sanitizer.items():
    sent = sent.replace(dirty, clean)
  return sent.strip()

def tokenize_sentences(document):
  """
  Breaks up document by sentence. Document should be a single string. Can be unsanitized.
  Returns sanitized broken up sentences
  """
  return nltk.tokenize.sent_tokenize(sanitize(document))

def summary_generator(sessionID, input_sentences, input_query, bsent):

  # Run MMR Ranking
  #---------------------------------------------------------------------------------
  # Description	: Code block that runs individual functions required to compute the MMR Score
  # Outputs 		: Table with sentences and their related scores computed by MMR
  #---------------------------------------------------------------------------------
  sentences = []
  lines=[]
  # queryWords = []
  queryWords = input_query

  sentences = sentences + process_file(sessionID, input_sentences)
  # lines = lines + returnLines(input_file_path)
  # linestring = " "
  # for line in lines:
  #     linestring = linestring + " " + line + " "
  # sen_len = len(linestring)
  sen_len = len(input_sentences)
  # calculate TF, IDF and TF-IDF scores
  IDF_w 		= IDFs(sentences)
  TF_IDF_w 	= TF_IDF(sentences)

  # build query; set the number of words to include in our query
  # queryWords.append(input_query)
  query = sentence.sentence("query", queryWords, queryWords)

  # pick a sentence that best matches the query
  # bstsen = 'Both Moderna and Pfizer require two initial doses, separated by about a month.'
  if len(bsent) <1:
    best1sentence = bsent
  else:
    best1sentence = bestSenPrep(sessionID, bsent)[0]
  # build summary by adding more relevant sentences
  summary = makeSummary(sentences, bsent, best1sentence, query, 0.01 * sen_len, IDF_w)
  # print('summary') 
  return summary


# KeyWord Extraction using RAKE
#---------------------------------------------------------------------------------
# Description	: Function to retrieve the KeyWords using RAKE and it's frequency
# Parameters	: sentences
# Return 		: Kewords, Frequency
#---------------------------------------------------------------------------------
def rakeQuery(lines):
  linestring = " "
  for line in lines:
    linestring = linestring + " " + line + " "
  text = linestring
  r = Rake(ranking_metric=Metric.WORD_FREQUENCY)
  r.extract_keywords_from_text(text)
  # Rp = r.get_ranked_phrases_with_scores()
  Rp = r.get_word_frequency_distribution()
  return Rp


# Function to preprocess the files in the document cluster before passing them into 
# the MMR summarizer system. Here the sentences of the document cluster are modelled 
# as sentences after extracting from the files in the folder path.
#---------------------------------------------------------------------------------
# Description	: Function to preprocess the files in the document cluster before
#				  passing them into the MMR summarizer system. Here the sentences
#				  of the document cluster are modelled as sentences after extracting
#				  from the files in the folder path. 
# Parameters	: file_name, name of the file in the document cluster
# Return 		: list of sentence object
#---------------------------------------------------------------------------------
def process_file(sessionID, input_sentences):

  # read file from provided folder path
  # f = open(file_name,'r')
  # text_0 = f.read()

  # replace all types of quotations by normal quotes
  #     text_1 = re.sub("\n"," ",text_0)

  #     text_1 = re.sub("\"","\"",text_1)
  #     text_1 = re.sub("''","\"",text_1)
  #     text_1 = re.sub("``","\"",text_1)

  #     text_1 = re.sub(" +"," ",text_1)

  #     # segment data into a list of sentences
  #     sentence_token = nltk.data.load('tokenizers/punkt/english.pickle')
  #     lines = sentence_token.tokenize(text_1.strip())
  lines = input_sentences


  # setting the stemmer
  sentences = []
  porter = nltk.PorterStemmer()

  # modelling each sentence in file as sentence object
  for line in lines:

    # original words of the sentence before stemming
    originalWords = line[:]
    line = line.strip().lower()

    # word tokenization
    sent = nltk.word_tokenize(line)

    # stemming words
    stemmedSent = [porter.stem(word) for word in sent]
    stemmedSent = list(filter(lambda x: x!='.'and x!='`'and x!=','and x!='?'and x!="'"
                                        and x!='!' and x!='''"''' and x!="''" and x!="'s", stemmedSent))
    # list of sentence objects

    if stemmedSent != []:
      sentences.append(sentence.sentence(sessionID, stemmedSent, originalWords))

  return sentences

# Function to find the term frequencies of the words in the sentences present in the provided document cluster
#---------------------------------------------------------------------------------
# Description	: Function to find the term frequencies of the words in the
#				  sentences present in the provided document cluster
# Parameters	: sentences, sentences of the document cluster
# Return 		: dictonary of word, term frequency score
#---------------------------------------------------------------------------------
def TFs(sentences):
  # initialize tfs dictonary
  tfs = {}

  # for every sentence in document cluster
  for sent in sentences:
    # retrieve word frequencies from sentence object
    wordFreqs = sent.getWordFreq()

    # for every word
    for word in wordFreqs.keys():
      # if word already present in the dictonary
      if tfs.get(word, 0) != 0:
        tfs[word] = tfs[word] + wordFreqs[word]
      # else if word is being added for the first time
      else:
        tfs[word] = wordFreqs[word]
  return tfs

# Function to find the inverse document frequencies of the words in the sentences present in the provided document cluster
#---------------------------------------------------------------------------------
# Description	: Function to find the inverse document frequencies of the words in
#				  the sentences present in the provided document cluster 
# Parameters	: sentences, sentences of the document cluster
# Return 		: dictonary of word, inverse document frequency score
#---------------------------------------------------------------------------------
def IDFs(sentences):
  N = len(sentences)
  idf = 0
  idfs = {}
  words = {}
  w2 = []
  # every sentence in our cluster
  for sent in sentences:
    # every word in a sentence
    # wordpre = sent.getPreProWords()
    for word in sent.getPreProWords():
      # for word in wordpre.keys():

      # not to calculate a word's IDF value more than once
      if sent.getWordFreq().get(word, 0) != 0:
        words[word] = words.get(word, 0)+ 1

  # for each word in words
  for word in words:
    n = words[word]

    # avoid zero division errors
    try:
      w2.append(n)
      idf = math.log10(float(N)/n)
    except ZeroDivisionError:
      idf = 0

    # reset variables
    idfs[word] = idf
  return idfs

# Function to find TF-IDF score of the words in the document cluster
#---------------------------------------------------------------------------------
# Description	: Function to find TF-IDF score of the words in the document cluster
# Parameters	: sentences, sentences of the document cluster
# Return 		: dictonary of word, TF-IDF score
#---------------------------------------------------------------------------------
def TF_IDF(sentences):
  # Method variables
  tfs = TFs(sentences)
  idfs = IDFs(sentences)
  retval = {}

  # for every word
  for word in tfs:
    #calculate every word's tf-idf score
    tf_idfs=  tfs[word] * idfs[word]

    # add word and its tf-idf score to dictionary
    if retval.get(tf_idfs, None) == None:
      retval[tf_idfs] = [word]
    else:
      retval[tf_idfs].append(word)

  return retval

# Function to find the sentence similarity for a pair of sentences by calculating cosine similarity
#---------------------------------------------------------------------------------
# Description	: Function to find the sentence similarity for a pair of sentences
#				  by calculating cosine similarity
# Parameters	: sentence1, first sentence
#				  sentence2, second sentence to which first sentence has to be compared
#				  IDF_w, dictinoary of IDF scores of words in the document cluster
# Return 		: cosine similarity score
#---------------------------------------------------------------------------------
def sentenceSim(sentence1, sentence2, IDF_w):
  numerator = 0
  denominator = 0
  denominator1 = 0

  for word in sentence2.getPreProWords():
    numerator+= sentence1.getWordFreq().get(word,0) * sentence2.getWordFreq().get(word,0) *  IDF_w.get(word,0) ** 2

  for word in sentence1.getPreProWords():
    denominator+= ( sentence1.getWordFreq().get(word,0) * IDF_w.get(word,0) ) ** 2

  for word in sentence2.getPreProWords():
    denominator1+= ( sentence2.getWordFreq().get(word,0) * IDF_w.get(word,0) ) ** 2

  # check for divide by zero cases and return back minimal similarity
  try:
    return numerator / (math.sqrt(denominator) * math.sqrt(denominator1))
  except ZeroDivisionError:
    return float("-inf")

# Function to create the summary set of a desired number of words
#---------------------------------------------------------------------------------
# Description	: Function to create the summary set of a desired number of words 
# Parameters	: sentences, sentences of the document cluster
#				  best_sentnece, best sentence in the document cluster
#				  query, reference query for the document cluster
#				  summary_length, desired number of words for the summary
#				  labmta, lambda value of the MMR score calculation formula
#				  IDF, IDF value of words in the document cluster 
# Return 		: name 
#---------------------------------------------------------------------------------
def makeSummary(sentences, bsent, best_sentence, query, summary_length, IDF):
  summary = [best_sentence]
  # print(best_sentence.getPreProWords())
  # print('summary',summary)
  # sum_len = len(best_sentence.getPreProWords())
  # print('sum_len',sum_len)
  MMRval={}
  dff = pd.DataFrame()
  sentRan = []
  mmrScr = []
  lScr = []
  rScr = []
  # keeping adding sentences until number of words exceeds summary length
  # while (sum_len < summary_length):
  MMRval={}
  lVal = {}
  rVal = {}

  for sent in sentences:
    MMRval[sent], lVal[sent], rVal[sent] = MMRScore(sent, query, bsent, summary, IDF)
  # maxxer = max(MMRval, key=MMRval.get)
  # summary.append(maxxer)
  # sentences.remove(maxxer)
  # sum_len += len(maxxer.getPreProWords())
  for j in MMRval:
    if len(j.getOriginalWords()) >14:
      sentRan.append(j.getOriginalWords())
      mmrScr.append(MMRval[j])
      lScr.append(lVal[j])
      rScr.append(rVal[j])
  dff['sent'] = sentRan
  # dff['score'] = mmrScr
  dff['lscore'] = lScr
  dff['rscore'] = rScr
  # dff = dff.sort_values(by=['score'], ascending = False)
  # return summary
  return dff

# Function to calculate the MMR score given a sentence, the query and the current best set of sentences
#---------------------------------------------------------------------------------
# Description	: Function to calculate the MMR score given a sentence, the query
#				  and the current best set of sentences
# Parameters	: Si, particular sentence for which the MMR score has to be calculated
#				  query, query sentence for the particualr document cluster
#				  Sj, the best sentences that are already selected
#				  lambta, lambda value in the MMR formula
#				  IDF, IDF value for words in the cluster
# Return 		: name 
#---------------------------------------------------------------------------------
def MMRScore(Si, query, bsent, Sj, IDF):
  Sim1 = sentenceSim(Si, query, IDF)
  # l_expr = lambta * Sim1
  l_expr = Sim1
  value = [float("-inf")]
  if len(bsent) > 0:
    for sent in Sj:
      Sim2 = sentenceSim(Si, sent, IDF)
      value.append(Sim2)

    # r_expr = (1-lambta) * max(value)
    r_expr = max(value)
    MMRScore = l_expr - r_expr
  else:
    MMRScore = l_expr
    r_expr = 0

  return MMRScore, l_expr, r_expr

# Function to prepare User selected summary sentence for MMR scoring function
#---------------------------------------------------------------------------------
# Description	: Function to prepare User selected summary sentence for MMR scoring function
# Parameters	: sentences
# Return 		: Sentence Object
#---------------------------------------------------------------------------------
def bestSenPrep(sessionID, senta):
  # sentence_token = nltk.data.load('tokenizers/punkt/english.pickle')
  # lines = sentence_token.tokenize(senta.strip())
  lines = senta
  # setting the stemmer
  sentences = []
  porter = nltk.PorterStemmer()
  # modelling each sentence in file as sentence object
  for line in lines:
    # original words of the sentence before stemming
    originalWords = line[:]
    line = line.strip().lower()
    # word tokenization
    sent = nltk.word_tokenize(line)
    # stemming words
    stemmedSent = [porter.stem(word) for word in sent]
    stemmedSent = list(filter(lambda x: x!='.'and x!='`'and x!=','and x!='?'and x!="'"
                                        and x!='!' and x!='''"''' and x!="''" and x!="'s", stemmedSent))
    # list of sentence objects
    if stemmedSent != []:
      sentences.append(sentence.sentence(sessionID, stemmedSent, originalWords))
  return sentences


def n_sim_sentences(top_sentences, other_sentences, all_sentences, n = N_SIM_SENTENCES):
  """
  This will return a dictionary whose keys are the sentences' strs. The values of the dictionary
   are n-length lists of str from most similar to least similar. This can probably be significantly optimized.
  :param top_sentences: The sentences around which to generate the cloud sentences.
                        NOTE: these are of the sentence class from sentence.py
  :type top_sentences: list[sentence.sentence]
  :param other_sentences: The sentence pool from which to draw the cloud sentences
  :type other_sentences: list[sentence.sentence]
  :param all_sentences: The entire set of sentences in the document
  :type all_sentences: list[sentence.sentence]
  :param n: The number of cloud sentences to generate
  :type n: int
  :return: A dict mapping the strings of the top_sentences to the cloud strings
  :rtype: dict[str, list[str]]
  """
  similarities = {}
  IDF = IDFs(all_sentences)
  for top_sentence in top_sentences:
    similarities[top_sentence.getOriginalWords()] = []  # hashing by entire sentence might be an inefficient way to do this, might not matter
    for other_sentence in other_sentences:
      similarities[top_sentence.getOriginalWords()].append((sentenceSim(top_sentence, other_sentence, IDF), other_sentence.getOriginalWords()))
  similarities = {k: sorted(v, reverse=True) for k, v in similarities.items()}#These comparisons should be memoized
  sim_sentences = {t_s.getOriginalWords(): [] for t_s in top_sentences}
  cloud_sents = set()
  indices = {t_s.getOriginalWords(): 0 for t_s in top_sentences}
  counts = {t_s.getOriginalWords() : 0 for t_s in top_sentences}
  for i in range(len(top_sentences) * n):
    best_sent = None
    best_sim = None
    for sent_obj in top_sentences:
      sent = sent_obj.getOriginalWords()
      if counts[sent] == n:
        continue
      ind = indices[sent]
      sim = similarities[sent][ind]
      if best_sim is None or sim[0] > best_sim[0]:
        best_sent = sent
        best_sim = sim
    if best_sent is None:
      break  # This triggers if there's not enough sentences to distribute
    sim_sentences[best_sent].append(best_sim[1])
    cloud_sents.add(best_sim[1])
    counts[best_sent] += 1
    while similarities[best_sent][indices[best_sent]][1] in cloud_sents:
      indices[best_sent] += 1
  return sim_sentences

