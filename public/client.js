 import { DEMO_ARTICLE_TITLE, DEMO_ARTICLE_SENTENCES, DEMO_ARTICLE_TEXT } from "./demo_article.js";
import { TOP_SENTENCES } from "./top_sentences.js";
import { autocomplete } from "./autocomplete.js";
import { uploadDocument, rank } from "./api.js";
import {View} from "./view.js";
const SlimSelect = window.SlimSelect;


let view;

// These change when a user uploads a new document
let rawSentences = []; // List: ID->sentence
let rawDocument = "";
let keywords = [];  // might not need this?
let sessionID = null;

// These are involved in the ranking.
let candidateSentences = []; // list: [{ID, lscore, rscore, score, rank, prev_rank}, ...]
let summarySentences = [];  // [IDs]
// let lambda = 0;  // TODO: make this a getter instead?

// Information about sentence selection
let selectedSentence = null;  // ID?

function getCurrentLambda() {
  let lambdaSlider = document.getElementById("lambdaSlider");
  // Note: the slider is an int from 0 to 100, but we want a float from 0 to 1.
  return lambdaSlider.valueAsNumber / 100.0;
}




////////////////////////
// Drop Handlers
////////////////////////

// Moving a sentence from candidates -> summary
function onDropInSummarySection(ev) {
  ev.preventDefault();
  let sentenceID = parseInt(ev.dataTransfer.getData("text/plain"));
  
  let newCandidates = candidateSentences.filter(c => (c.ID != sentenceID));
  if (newCandidates.length === candidateSentences.length) return; // Wasn't a candidate sentence
  
  summarySentences.push(sentenceID);
  candidateSentences = newCandidates;
  
  // We need to redraw the summary and rerank :)
  view.renderSummary(summarySentences, rawSentences);
  handleRerankClick();  // Need to rerank now that we have a new summary sentence
}

// Moving a sentence from summary -> candidates
function onDropInCandidatesSection(ev) {
  ev.preventDefault();
  let sentenceID = parseInt(ev.dataTransfer.getData("text/plain"));
  
  if (!summarySentences.includes(sentenceID)) return;
  
  summarySentences = summarySentences.filter(id => id != sentenceID);
  candidateSentences.push({ID: sentenceID});
  
  view.renderSummary(summarySentences, rawSentences);
  handleRerankClick();  // Need to rerank now that the summary sentences have changed.
}




/////////////////////////////////
// Functions dealing w/ ranking
/////////////////////////////////

// When lambda changes, we trigger a rerank, but don't need to ping the backend
function handleLambdaChange() {
  if (candidateSentences.length < 1) return;
  
  let lambda = getCurrentLambda();
  // console.log("revamping sentences because of new lambda!", lambda);
  // console.log("before candidates:", candidateSentences);
  
  candidateSentences = candidateSentences.map(s => {
    s.score = lambda*s.lscore - (1-lambda)*s.rscore;
    return s;
  });
  candidateSentences.sort((c1, c2) => (c1.score < c2.score ? 1 : (c1.score > c2.score ? -1 : 0)));
  candidateSentences = candidateSentences.map((candidate, idx) => {
    candidate.prev_rank = candidate.rank;
    candidate["rank"] = idx + 1;
    return candidate;
  });
  
  // console.log("after candidates:", candidateSentences);
  view.renderCandidates(candidateSentences, lambda, rawSentences);
}

// This is called when we get back ranking results from the backend.
function handleRerankResult(res) {
  res = JSON.parse(res);
  
  if (candidateSentences.length < 1) {
    // i.e. we haven 't clicked "rank" yet for this document, and all the sentences are candidates with no previous scores. 
    candidateSentences = rawSentences.map((s, idx) => ({ID: idx}));
  }
  
  console.log("candidate sentences:", candidateSentences);
  
  let lambda = getCurrentLambda();
  let idToPreviousRank = new Map(candidateSentences.map(c => [c.ID, c.rank]));
  
  candidateSentences = res["sen_scores"].map(s => ({
    ID: s.sentenceID,
    lscore: s.LSimScr,
    rscore: s.RSimScr,
    score: lambda*s.LSimScr - (1-lambda)*s.RSimScr,
    prev_rank: idToPreviousRank.get(s.sentenceID),
  }));
  candidateSentences.sort((c1, c2) => (c1.score < c2.score ? 1 : (c1.score > c2.score ? -1 : 0)));
  candidateSentences = candidateSentences.map((candidate, idx) => {
    candidate["rank"] = idx + 1;
    return candidate;
  });
  
  view.renderCandidates(candidateSentences, lambda, rawSentences);
}

// Ping the backend to get a new ranking.
function handleRerankClick() {
  
  if (sessionID === null) {
    alert("Please upload a document first!");
    return;
  }
  
  // TODO: delete when no longer needed
  let mock_rank = (session, kws, summary, cb) => {
    let res = {};
    res["sen_scores"] = rawSentences
      .filter((_, id) => !summary.includes(id))
      .map((sentence, id) => ({
        sentenceID: id,
        LSimScr: Math.random(),
        RSimScr: Math.random()
      }));
    cb(JSON.stringify(res));
  };
  
  // TODO: switch to the real rank :)
  mock_rank(sessionID, query_slimSelect.selected(), summarySentences, handleRerankResult);
}






/////////////////////////////////
// Upload function
/////////////////////////////////

var query_slimSelect = new SlimSelect({
  select: '#query',
  hideSelectedOption: true,
});

window.sselect = query_slimSelect;  // for debugging :)

// use this formatting to update the options for keywords
//query_slimSelect.setData([
//  {text: 'value1', innerHTML: "<p>something</p>"},
//  {text: 'value2', data : 2}
//])

let uploadClickHandler = function() {
  let rawdoc = document.getElementById("rawdoctextarea").value;
  
  // save the sessionID
  let uploadSuccessFn = function(res) {
    res = JSON.parse(res);
        
    // Set global variables.
    sessionID = res["session_id"];
    rawSentences = res["sentences"].map(s=>s[0]);
    keywords = res["keywords"];  // TODO: possibly map
    rawDocument = rawdoc;
    
    // reset some variables
    candidateSentences = [];
    summarySentences = [];
    
    // Set up the keyword/query box
    let keywords_data = [];
    let keywords_len = keywords.length;
    let idx = 0;
    for (let s of keywords) {
      idx = idx + 1;
      let curr_obj = {};
      let bl = "100";
      let gr = ((keywords_len-idx)*255/keywords_len).toString();
      let rd = ((idx)*255/keywords_len).toString();
      console.log(s);
      curr_obj.text = `${s[0]} (${s[1]})`;
      curr_obj.innerHTML = "<div>" +s[0] +"</div>"+ '<div style="color:rgb('+ rd +' ,'+gr+' ,'+bl+' );">('+s[1]+')</div>';
      curr_obj.value = s[0];
      keywords_data.push(curr_obj);
    }
    // console.log(keywords_data);
    query_slimSelect.setData(keywords_data);
    
    // select the top 5 keywords to start
    for (let s of keywords.slice(0, 5)) {
      query_slimSelect.setSelected(s[0]);
    }
    
    // display the raw document
    view.renderRawDocument(rawDocument, rawSentences);
    // discard current summary
    view.resetSummary();
  };
  
  let uploadErrorFn = function(res) {
    document.getElementById("upload-results-error").innerHTML = res;
  };

  uploadDocument(rawdoc, uploadSuccessFn, uploadErrorFn);
  document.getElementById("btn-modal-close").click();

};

// Any initialization code that accesses HTML elements in the document should
// go here. This will be called once the page is fully loaded.
window.onload = function() {
  // Click the upload button on startup
  document.getElementById("upload-button").click();
  
  document.getElementById("rawdoctextarea").value = DEMO_ARTICLE_TEXT;  // TODO: get rid of this, or change it to be a button
  
  view = new View(
    document.getElementById("document-view"),
    document.getElementById("ranking-view"),
    document.getElementById("summary-view"));

  // TODO connect functionality for the upload button in the modal
  console.log("something here");
  let uploadButtonModal = document.getElementById("upload_button_modal");
  uploadButtonModal.onclick = uploadClickHandler;

  let lambdaSlider = document.getElementById("lambdaSlider");
  lambdaSlider.onchange = handleLambdaChange;

  let rankButton = document.getElementById("rank-button");
  rankButton.onclick = handleRerankClick;
  
  document.getElementById("summary-view").ondragover = (ev => ev.preventDefault());
  document.getElementById("summary-view").ondrop = onDropInSummarySection;
  
  document.getElementById("ranking-view").ondragover = (ev => ev.preventDefault());
  document.getElementById("ranking-view").ondrop = onDropInCandidatesSection;



  /*initiate the autocomplete function on the "myInput" element, and pass along the countries array as possible autocomplete values:*/
  // autocomplete(document.getElementById("myKeywords"), keywords);

  // Set up the sentences.
  // populateRankedSentences(candidates);  // Wait until Rank is pressed
  // populateSummary(summary); // lol, this is empty

  // Set up the click handlers on the left and right buttons
  // document
  //   .getElementById("candidate-to-summary")
  //   .addEventListener("click", moveSelection, false);
  // document
  //   .getElementById("summary-to-candidate")
  //   .addEventListener("click", moveSelection, false);
};








/*
 *
 *
 * Land of old cruft!
 *
 *
 */


/*
JS tips
------------

Debugging:
  - To try stuff out in an interpreter, you can use the JavaScript Console
    in your browser's dev tools. For Chrome, that's
    View > Developer > JavaScript Console.
  - The console (above) is also SUPER good for testing things out. If you open
    it up on our webpage, you can run any of the functions we've defined below.
  - To inspect HTML in the browser, right click then hit inspect.
  - Equivalent of print is console.log()
*/



// // All sentences, with their original index :)
// let candidates = TOP_SENTENCES.map(function(txt, idx) {
//   return {
//     text: txt,
//     id: idx
//   };
// });

// Summary sentences should also look like {text: 'blah', id: 2}. Just move over objects from 'candidates' directly.
// let summary = [];

// This is the 'id' of the selected sentence, whether the selection is from the summary or candidate set.
// TODO: wrap these up into a class or something...
// let selectedCandidate = -1;
// let selectedSummary = -1;
// let unselectCurrentElement = function() {};

// initialize sessionID to be empty. This will be updated every time a new upload happens
// let sessionID = "";

// function getCurrentQuery() {
//   let textboxElement = document.getElementById("myKeywords");
//   let query = textboxElement.value;
//   // We might want to trim whitespace, split words, etc.
//   console.log(query);
//   return query;
// }

// function to shuffle the array
// function shuffle(array) {
//   let currentIndex = array.length,
//     randomIndex;

//   // While there remain elements to shuffle...
//   while (currentIndex != 0) {
//     // Pick a remaining element...
//     randomIndex = Math.floor(Math.random() * currentIndex--);

//     // And swap it with the current element.
//     [array[currentIndex], array[randomIndex]] = [
//       array[randomIndex],
//       array[currentIndex]
//     ];
//   }

//   return array;
// }

// Populate the "ranking-view" with each sentence in "candidates" (defined at top)
// function populateRankedSentences(sentences) {
//   // Clear the current contents
//   let rankDiv = document.getElementById("ranking-view");
//   rankDiv.innerHTML = "";

//   for (let sentence of sentences.slice(0, 20)) {
//     // Going to create some HTML that looks like:
//     //   <div class="card"><div class="card-body">TEXT</div></div>
//     let outer = document.createElement("div");
//     outer.classList.add("card");
//     outer.classList.add("candidate-card");
//     // Probably a nicer way to do this -.-
//     outer.addEventListener(
//       "click",
//       function() {
//         console.log("clicked");
//         if (selectedCandidate === sentence.id) {
//           unselectCurrentElement();
//           // outer.classList.remove('selected');
//           selectedCandidate = -1;
//           unselectCurrentElement = () => {};
//           document.getElementById("candidate-to-summary").disabled = true;
//         } else {
//           unselectCurrentElement();
//           outer.classList.add("selected");
//           selectedCandidate = sentence.id;
//           selectedSummary = -1;
//           unselectCurrentElement = () => outer.classList.remove("selected");
//           document.getElementById("summary-to-candidate").disabled = true;
//           document.getElementById("candidate-to-summary").disabled = false;
//         }
//       },
//       true
//     ); // Add onclick eventListener

//     let inner = document.createElement("div");
//     inner.classList.add("card-body");

//     let text = document.createTextNode(sentence.text);

//     // Assemble!
//     rankDiv.appendChild(outer);
//     outer.appendChild(inner);
//     inner.appendChild(text);
//   }
// }

// // Populate the "summary-view" with each sentence in "summary" (defined at top)
// function populateSummary(summarySentences) {
//   // clear the summary
//   let summaryDiv = document.getElementById("summary-view");
//   summaryDiv.innerHTML = "";

//   // For each sentence in the summary, add a new div.
//   for (let s of summarySentences) {
//     let outer = document.createElement("div");
//     outer.classList.add("card");
//     outer.classList.add("candidate-card");
//     outer.addEventListener(
//       "click",
//       function() {
//         console.log("clicked");
//         // TODO: factor this out into its own function, probably...
//         if (selectedSummary === s.id) {
//           unselectCurrentElement();
//           outer.classList.remove("selected");
//           selectedSummary = -1;
//           unselectCurrentElement = () => {};
//           document.getElementById("summary-to-candidate").disabled = true;
//         } else {
//           unselectCurrentElement();
//           outer.classList.add("selected");
//           selectedCandidate = -1;
//           selectedSummary = s.id;
//           unselectCurrentElement = () => outer.classList.remove("selected");
//           document.getElementById("summary-to-candidate").disabled = false;
//           document.getElementById("candidate-to-summary").disabled = true;
//         }
//       },
//       true
//     ); // Add onclick eventListener

//     let inner = document.createElement("div");
//     inner.classList.add("card-body");

//     let text = document.createTextNode(s.text);

//     // Assemble!
//     summaryDiv.appendChild(outer);
//     outer.appendChild(inner);
//     inner.appendChild(text);
//   }
// }

// This function gets called whenever one of the -> or <- buttons gets pressed.
// function moveSelection() {
//   if (selectedCandidate >= 0) {
//     console.log("starting to move the candidate");
//     let sentence = candidates.find(s => s.id === selectedCandidate);
//     if (sentence === undefined) {
//       console.log("This shouldn't happen!");
//       return;
//     }
//     // Update candidates and summary
//     candidates = candidates.filter(s => s.id !== selectedCandidate);
//     summary.push(sentence);

//     selectedCandidate = -1;
//     selectedSummary = -1;
//     document.getElementById("summary-to-candidate").disabled = true;
//     document.getElementById("candidate-to-summary").disabled = true;
//   } else if (selectedSummary >= 0) {
//     let sentence = summary.find(s => s.id === selectedSummary);
//     if (sentence === undefined) {
//       console.log("This shouldn't happen!");
//       return;
//     }
//     // Update candidates and summary
//     summary = summary.filter(s => s.id !== selectedSummary);
//     candidates.unshift(sentence); // Add it to the front to make sure we can see it? Hack for the prototype ;p

//     selectedCandidate = -1;
//     selectedSummary = -1;
//     document.getElementById("summary-to-candidate").disabled = true;
//     document.getElementById("candidate-to-summary").disabled = true;
//   }

//   // Now: rerender!
//   populateRankedSentences(candidates);
//   populateSummary(summary);

//   handleRerank();
// }


// var sentences;
// var keywords;