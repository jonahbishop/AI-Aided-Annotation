import random

import mmr
import server
from random import randrange

DATA = "F.D.A. to Allow ‘Mix and Match’ Approach for Covid Booster Shots.\n\nThe agency may act this week, when it is expected to authorize booster shots for recipients of the Moderna and Johnson & Johnson vaccines.\n\nThe Food and Drug Administration is planning to allow Americans to receive a different Covid-19 vaccine as a booster than the one they initially received, a move that could reduce the appeal of the Johnson & Johnson vaccine and provide flexibility to doctors and other vaccinators.\n\nThe government would not recommend one shot over another, and it might note that using the same vaccine as a booster when possible is preferable, people familiar with the agency’s planning said. But vaccine providers could use their discretion to offer a different brand, a freedom that state health officials have been requesting for weeks.\n\nThe approach was foreshadowed on Friday, when researchers presented the findings of a federally funded “mix and match” study to an expert committee that advises the Food and Drug Administration. The study found that recipients of Johnson & Johnson’s single-dose shot who received a Moderna booster saw their antibody levels rise 76-fold in 15 days, compared with only a fourfold increase after an extra dose of Johnson & Johnson.\n\nFederal regulators this week are aiming to greatly expand the number of Americans eligible for booster shots. The F.D.A. is expected to authorize boosters of the Moderna and Johnson & Johnson vaccines by Wednesday evening; it could allow the mix-and-match approach by then. The agency last month authorized booster shots of the Pfizer-BioNTech vaccine for at least six months after the second dose.\n\nAn advisory committee of the Centers for Disease Control and Prevention will take up the booster issue on Thursday; the agency will then issue its own recommendations. By the end of the week, tens of millions more Americans could be eligible for extra shots.\n\nThe study presented to the F.D.A.’s advisory panel last week, conducted by the National Institutes of Health, suggested that Johnson & Johnson recipients might benefit most from a booster shot of the Moderna vaccine. A shot of the Pfizer-BioNTech vaccine also raised the antibody levels of Johnson & Johnson recipients more than Johnson & Johnson did, the study found, although not as much as Moderna did. The N.I.H. researchers tested a full dose of Moderna’s vaccine for a booster shot, but regulators are also considering whether to authorize a half dose.\n\nExperts emphasized last week that the new data was based on small groups of volunteers and short-term findings. Only antibody levels — one measure of the immune response — were calculated as part of the preliminary data, not the levels of immune cells primed to attack the coronavirus, which scientists say are also an important measure of a vaccine’s success.\n\nThe study’s researchers warned against using the findings to conclude that any one combination of vaccines was better. The study “was not powered or designed to compare between groups,” said Dr. Kirsten E. Lyke, a professor at the University of Maryland School of Medicine, who presented the data.\n\nWhile the research on mixing and matching doses is somewhat thin, even some scientists who have strongly criticized the Biden administration’s booster policy said that providers should be given a measure of discretion as the campaign ramps up.\n\n“If you look at the data, it certainly looks like it might be better,” Dr. Paul A. Offit, the director of the Vaccine Education Center at Children’s Hospital of Philadelphia, said of Moderna or Pfizer boosters for Johnson & Johnson recipients. “I think we should move quickly on this, because it’s already happening.”\n\nAt the meeting on Friday of the Food and Drug Administration’s expert panel, of which Dr. Offit is a member, top C.D.C. officials argued that providers needed latitude to offer different vaccines as boosters because patients might have had adverse reactions after their initial shots or presented other new concerns. Providers also might not have access to a vaccine a patient initially received, they said.\n\nThe federal government will cover the cost of a different vaccine as a booster only if the Food and Drug Administration authorizes the approach, officials said.\n\n“I’d like to reiterate how important it is from a programmatic perspective to have a little bit of flexibility,” Dr. Melinda Wharton, a top vaccine official at the C.D.C., told the F.D.A. panel.\n\n“From a public health perspective, there’s a clear need in some situations for individuals to receive a different vaccine,” said Dr. Amanda Cohn, another high-ranking C.D.C. official.\n\nBoth Moderna and Pfizer require two initial doses, separated by about a month. Regulators are expected to follow the same approach they took with Pfizer’s vaccine and authorize a booster of Moderna’s vaccine about six months after the second shot. Johnson & Johnson is headed for a booster shot of its vaccine at least two months after the first dose.\n\nState health officials have been arguing for weeks that recipients of booster shots should not be strictly bound to the vaccine they initially received, for reasons such as supply, patient choice and ease of administration.\n\n“The No. 1 thing I heard from state health secretaries was the need for permissive language around a mix-and-match approach,” said Dr. Nirav D. Shah, Maine’s top health official and the president of the Association of State and Territorial Health Officials.\n\nDr. Clay Marsh, West Virginia’s Covid-19 czar, said the state had a greater supply of Moderna and Pfizer-BioNTech vaccines than of Johnson & Johnson’s, so officials there might prefer to use them for boosters out of convenience. Others said the option of switching vaccines could streamline the administration of boosters.\n\n“The impetus for states and local health departments was that if they were going to go out to a community site or long-term care facility and start providing boosters, it was a little inefficient to show up somewhere and say, ‘We’re just doing the people who got Pfizer,’” said Dr. Marcus Plescia, the chief medical officer for the Association of State and Territorial Health Officials. “When you have a captive audience, you want to take advantage of that.”\n\nYet more options could lead to more confusion about booster shots, some experts have said. The Food and Drug Administration this week is expected to authorize boosters for all Johnson & Johnson recipients 18 and older. But the only Moderna recipients who are expected to become eligible for boosters are those who are at least 65 or otherwise considered at high risk, following the same eligibility requirements for recipients of Pfizer-BioNTech’s vaccine.\n\nJeannette Y. Lee, a biostatistician at the University of Arkansas for Medical Sciences and a member of the F.D.A.’s expert committee, warned on Friday that allowing people to switch from their original vaccine type could be “very, very messy in terms of the messaging.”\n\nIt remains unclear what dosage of Moderna’s vaccine might be authorized for use as a booster for recipients of other vaccines. Last week, the advisory committee voted unanimously to recommend that Moderna recipients receive a third shot of that vaccine as a booster, but at only half a dose.\n\nDr. Anthony S. Fauci, the government’s top infectious disease expert, publicly suggested on Sunday that the government was headed toward granting greater leeway, at least for Johnson & Johnson recipients. “I believe there’s going to be a degree of flexibility of what a person who got the J.&J. originally can do, either with J.&J. or with the mix-and-match from other products,” he said on “Fox News Sunday.”\n\nJust over 15 million people have been fully vaccinated with Johnson & Johnson’s vaccine, compared with 69.5 million for Moderna’s and 104.5 million with Pfizer-BioNTech’s."
# DATA = open("public/data/COVIDVaccine_article.txt", "r", encoding="utf-8").read() #NOT THE SAME, CHECK demo_article.js TO SEE WHY
result = None

def _redirect_server_json_requests(my_json):
  server.json_request = lambda s="": my_json[s] if s else my_json

def setup_dummy_session(data):
  sentences = mmr.tokenize_sentences(data)
  keyw_r = mmr.keyword_generator(sentences)
  bad_sentences = [(sentences[i], i) for i in range(0, len(sentences))]
  sessionID = randrange(1, 10000)
  server.SESSIONS[sessionID] = {
    "raw_document": data,
    "sentences": bad_sentences,
    "keywords": keyw_r,
  }
  print(f"Started dummy session {sessionID}")
  return sessionID


def test_mmr_cloud():
  sessionID = 5
  sentence_choices = [2, 38, 7]
  sents = mmr.tokenize_sentences(DATA)
  sents = mmr.processFile(sessionID, sents)
  top_sents = [sents[x] for x in sentence_choices]
  other_sents = [sents[x] for x in range(len(sents)) if x not in sentence_choices]
  n_sims = mmr.n_sim_sentences(top_sents, other_sents, sents)
  for top in n_sims:
    print("\n\t+ ".join([top, *n_sims[top]]))
  return n_sims


def test_server_cloud(data = DATA, top_sentence_IDs = None):
  if top_sentence_IDs is None:
    top_sentence_IDs = [2, 38, 7]
  sessionID = setup_dummy_session(DATA)
  result = server._testable_phase_two(sessionID, top_sentence_IDs)
  print("\n---------------------\nTesting Results:\n---------------------")
  for top in result:
    print("\n\t+ ".join([str(top), *[str(x) for x in result[top]]]))

def test_rank():
  s_id = setup_dummy_session(DATA)
  my_json = {"session_id": s_id, "keywords": ["johnson", "vaccine", "booster", "moderna", "said"], "summary": []}
  _redirect_server_json_requests(my_json)
  res = server.rank()
  print(res)
  return res

def test_json_file():
  s_id = setup_dummy_session(DATA)
  my_sum = {"Top_sentence_A" : (["Cloud_sent_AA", "Cloud_sent_AB", "Cloud_sent_AC"], ["Alex Trebek?", "What?", "Where"]),
             "Top_sentence_B" : (["Cloud_sent_BA", "Cloud_sent_BB", "Cloud_sent_BC"], ["Why?", "When?", "How?"])}
  my_json = {"session_id" : s_id, "full_summary": my_sum}
  _redirect_server_json_requests(my_json)
  server.generate_json()


if __name__ == '__main__':
  # test_server_cloud()
  # test_rank()
  # test_mmr_cloud()
  test_json_file()
