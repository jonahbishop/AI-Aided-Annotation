import {DEMO_ARTICLE_TITLE, DEMO_ARTICLE_SENTENCES} from "./demo_article.js";
import {TOP_SENTENCES} from "./top_sentences.js";
import {autocomplete, keywords} from "./autocomplete.js";
import {uploadDocument} from "./api.js";

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


// All sentences, with their original index :)
let candidates = TOP_SENTENCES.map(function(txt, idx) {
  return {
    text: txt,
    id: idx,
  }
});

// Summary sentences should also look like {text: 'blah', id: 2}. Just move over objects from 'candidates' directly.
let summary = [];

// This is the 'id' of the selected sentence, whether the selection is from the summary or candidate set. 
// TODO: wrap these up into a class or something...
let selectedCandidate = -1; 
let selectedSummary = -1;
let unselectCurrentElement = function(){};




function getCurrentLambda() {
  let lambdaSlider = document.getElementById("lambdaSlider");
  handleRerank();
  // Note: the slider is an int from 0 to 100, but we want a float from 0 to 1.
  return lambdaSlider.valueAsNumber / 100.0;
}



function getCurrentQuery() {
  let textboxElement = document.getElementById("myKeywords");
  let query = textboxElement.value;
  // We might want to trim whitespace, split words, etc.
  console.log(query);
  return query;
}

// function to respond to rank button click
function handleRerank() {
  console.log(getCurrentQuery());
  console.log("reranking triggered!");
  // TODO: stuff!
  shuffle(candidates);
  populateRankedSentences(candidates);
}

// function to shuffle the array
function shuffle(array) {
  let currentIndex = array.length,  randomIndex;

  // While there remain elements to shuffle...
  while (currentIndex != 0) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex--);

    // And swap it with the current element.
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex], array[currentIndex]];
  }

  return array;
}

// Populate the "ranking-view" with each sentence in "candidates" (defined at top)
function populateRankedSentences(sentences) {  
  // Clear the current contents
  let rankDiv = document.getElementById("ranking-view");
  rankDiv.innerHTML = "";
  
  for (let sentence of sentences.slice(0, 20)) {
    // Going to create some HTML that looks like:
    //   <div class="card"><div class="card-body">TEXT</div></div>
    let outer = document.createElement("div");
    outer.classList.add("card");
    outer.classList.add("candidate-card");
    // Probably a nicer way to do this -.-
    outer.addEventListener("click", function() {
      console.log('clicked');
      if (selectedCandidate === sentence.id) {
        unselectCurrentElement();
        // outer.classList.remove('selected');
        selectedCandidate = -1;
        unselectCurrentElement = () => {};
        document.getElementById("candidate-to-summary").disabled = true;
      } else {
        unselectCurrentElement();
        outer.classList.add('selected');
        selectedCandidate = sentence.id;
        selectedSummary = -1;
        unselectCurrentElement = () => outer.classList.remove('selected');
        document.getElementById("summary-to-candidate").disabled = true;
        document.getElementById("candidate-to-summary").disabled = false;

      }
    }, true); // Add onclick eventListener 

    let inner = document.createElement("div");
    inner.classList.add("card-body");

    let text = document.createTextNode(sentence.text);

    // Assemble!
    rankDiv.appendChild(outer);
    outer.appendChild(inner);
    inner.appendChild(text);
  }
}


// Populate the "summary-view" with each sentence in "summary" (defined at top)
function populateSummary(summarySentences) {
  // clear the summary
  let summaryDiv = document.getElementById("summary-view");
  summaryDiv.innerHTML = "";
  
  // For each sentence in the summary, add a new div.
  for (let s of summarySentences) {
    let outer = document.createElement("div");
      outer.classList.add("card");
      outer.classList.add("candidate-card");
      outer.addEventListener("click", function() {
        console.log('clicked');
        // TODO: factor this out into its own function, probably...
        if (selectedSummary === s.id) {
          unselectCurrentElement();
          outer.classList.remove('selected');
          selectedSummary = -1;
          unselectCurrentElement = () => {};
          document.getElementById("summary-to-candidate").disabled = true;
        } else {
          unselectCurrentElement();
          outer.classList.add('selected');
          selectedCandidate = -1;
          selectedSummary = s.id;
          unselectCurrentElement = () => outer.classList.remove('selected');
          document.getElementById("summary-to-candidate").disabled = false;
          document.getElementById("candidate-to-summary").disabled = true;
        }
      }, true); // Add onclick eventListener 

    let inner = document.createElement("div");
    inner.classList.add("card-body");

    let text = document.createTextNode(s.text);

    // Assemble!
    summaryDiv.appendChild(outer);
    outer.appendChild(inner);
    inner.appendChild(text);
  }
}

// This function gets called whenever one of the -> or <- buttons gets pressed.
function moveSelection() {
  if (selectedCandidate >= 0) {
    console.log("starting to move the candidate");
    let sentence = candidates.find(s => s.id === selectedCandidate);
    if (sentence === undefined) {
      console.log("This shouldn't happen!");
      return;
    }
    // Update candidates and summary
    candidates = candidates.filter(s => s.id !== selectedCandidate);
    summary.push(sentence);
    
    selectedCandidate = -1;
    selectedSummary = -1;
    document.getElementById("summary-to-candidate").disabled = true;
    document.getElementById("candidate-to-summary").disabled = true;
  } else if (selectedSummary >= 0) {
    let sentence = summary.find(s => s.id === selectedSummary);
    if (sentence === undefined) {
      console.log("This shouldn't happen!");
      return;
    }
    // Update candidates and summary
    summary = summary.filter(s => s.id !== selectedSummary);
    candidates.unshift(sentence);  // Add it to the front to make sure we can see it? Hack for the prototype ;p
    
    selectedCandidate = -1;
    selectedSummary = -1;
    document.getElementById("summary-to-candidate").disabled = true;
    document.getElementById("candidate-to-summary").disabled = true;
  }
  
  // Now: rerender!
  populateRankedSentences(candidates);
  populateSummary(summary);
  
  handleRerank();
}




// Any initialization code that accesses HTML elements in the document should
// go here. This will be called once the page is fully loaded.
window.onload = function() {
  let lambdaSlider = document.getElementById("lambdaSlider");
  lambdaSlider.onchange = function() {
    console.log("slider changed! New Value: ", getCurrentLambda());
  }

  let rankButton = document.getElementById("rank-button");
  rankButton.onclick = handleRerank;
  
  // TODO: implement uploading. Maybe it just brings up a modal with a text-area for now (not file upload)
  document.getElementById("upload-button").onclick = () => {
    uploadDocument("Test document! This is a test.", () => {});
    // alert("Not implemented!");
  };
  
  /*initiate the autocomplete function on the "myInput" element, and pass along the countries array as possible autocomplete values:*/
  autocomplete(document.getElementById("myKeywords"), keywords);
  
  // Set up the sentences.
  // populateRankedSentences(candidates);  // Wait until Rank is pressed
  populateSummary(summary);  // lol, this is empty
  
  // Set up the click handlers on the left and right buttons
  document.getElementById("candidate-to-summary").addEventListener("click", moveSelection, false);
  document.getElementById("summary-to-candidate").addEventListener("click", moveSelection, false);
}
