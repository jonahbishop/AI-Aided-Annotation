// The "View" class handles how to render stuff to the page.

export class View {
  constructor(rawDocumentContainer, candidatesContainer, summaryContainer, keywordsContainer) {
    this.rawDocumentContainer = rawDocumentContainer;
    this.candidatesContainer = candidatesContainer;
    this.summaryContainer = summaryContainer;
    
    this.keywordsContainer = keywordsContainer;  // NOTE: this might be handled differently w/ that library
    
    // TODO: add mappings from sentence ID -> div/span/etc. so that we can easily "select" or "deselect" a sentence, or otherwise
    // highlight it. These can be populated whenever we call renderCandidates, renderRawDocuemnt, and renderSummary.
    this.candidateIDToContainer = {};
    this.summaryIDToContainer = {};
    
  }
  
  renderRawDocument(rawDocument, sentences) {
    
    this.rawDocumentContainer.innerHTML = "";
    
    console.log("INCLUDES TEST: ");
    for (let s of sentences) {
      if (!rawDocument.includes(s)) {
        console.log(s);
      }
    }
    
    
    // This is very not robust :)
    for (let paragraph of rawDocument.split("\n\n")) {
      let p = document.createElement("p");
      let txt = document.createTextNode(paragraph);
      
      this.rawDocumentContainer.append(p);
      p.append(txt);
    }
    
    // TODO: do the best we can to wrap each sentence in a span w/ an ID :)
  }
  
  // renderKeywords(keywords) {
  //   // TODO: integrate the code from client.js into here OR just handle keywords in client.js and delete this.
  // }
  
  
  makeScoreVisualization(lscore, rscore, score) {
    let row = document.createElement("div");
    row.classList.add("row");
    let container = document.createElement("div");
    container.classList.add("col-12");
    
    let minScore = -rscore;
    let maxScore = lscore;
    
    let leftBoundary = 125 + 100*minScore;
    let mid = 125 + 100*score;
    let rightBoundary = 125 + 100*maxScore;
    let prettyScore = Math.round(score * 100) / 100;
    // let prettyScore = score;
    
  
    container.innerHTML = `
    <svg width="256px" height="40px">
    
      <rect x="${leftBoundary}" y="12" rx="1" ry="1" width="${mid-leftBoundary}" height="6"
            style="fill:green;opacity:0.5" />
            
      <rect x="${mid}" y="12" rx="1" ry="1" width="${rightBoundary-mid}" height="6"
            style="fill:red;opacity:0.5" />
            
        <line x1="${mid}" y1="7" x2="${mid}" y2="23" style="stroke:rgb(140,140,140);stroke-width:1" />
        <text x="${mid}" y="33" font-size="10px" fill="grey">${prettyScore}</text>
    </svg>
    `;
    
    row.appendChild(container);
    return row;
    
  }
  
  // TODO: complete this function. Document what 'candidates' is :)
  renderCandidates(candidates, lambda, rawSentences) {
    // console.log("candidates: ", candidates);
    // console.log("raw sentences: ", rawSentences);
    
    // candidates is a list: [{ID, lscore, rscore, score, rank, prev_rank}, ...]
    
    this.candidatesContainer.innerHTML = "";  // reset the container
    this.candidateIDToContainer = {};
        
    for (let candidate of candidates.slice(0, 25)) {
    // for (let candidate of candidates.slice(0, 5)) {
      // We're going to create HTML that looks like this:
      /*
      <div class="card card-candidate">
        <div class="card-body">
          <div class="row">
            <div class="col-10"> [sentence goes here] </div>
            <div class="col-2"> +5 </div>
          </div>
          
          [score visualization goes here]
          
        </div>
      </div>
      */
      let outer = document.createElement("div");
      outer.classList.add("card");
      outer.classList.add("candidate-card");
      this.candidateIDToContainer[candidate.ID] = outer;
      
      // allow drag
      outer.draggable = true;
      outer.addEventListener("dragstart", ev => {ev.dataTransfer.setData("text/plain", `${candidate.ID}`)});
      
      // TODO: implement selection :D
      outer.addEventListener("click", function() {console.log("clicked: ", candidate.ID)}, true);
      
      let cardBody = document.createElement("div");
      cardBody.classList.add("card-body");
      
      let row = document.createElement("div");
      row.classList.add("row");
      
      let sentenceCol = document.createElement("div");
      sentenceCol.classList.add("col-10");
      
      let rankChangeCol = document.createElement("div");
      rankChangeCol.classList.add("col-2");
      
      let sentence = rawSentences[candidate.ID];
      let sentenceText = document.createTextNode(sentence);
      
      let [r, prevR] = [candidate.rank, candidate.prev_rank];
      let rankChange = "";
      if (r && prevR && r !== prevR) {
        let delta = prevR - r;
        rankChange = `${delta > 0 ? '+' : ''}${delta}`;
      }
      rankChange = document.createTextNode(rankChange);
      
      let scoreViz = this.makeScoreVisualization(candidate.lscore, candidate.rscore, candidate.score);
      // TODO: add a visualization of the score!!!

      // Assemble!
      // Note: It'd be clearer if we just set innerHTML... 
      this.candidatesContainer.appendChild(outer);
      outer.appendChild(cardBody);
      cardBody.appendChild(row);
      row.appendChild(sentenceCol);
      sentenceCol.appendChild(sentenceText);
      row.appendChild(rankChangeCol);
      rankChangeCol.appendChild(rankChange);
      cardBody.appendChild(scoreViz);
    }
  }
  
  resetSummary() {
    this.summaryContainer.innerHTML = `<div class="p-2 summary-default">Drag sentences here to create your summary. </div>`;
  }
  
  // summarySentences: List[IDs]
  // rawSentences: List[Text]  (index is ID)
  renderSummary(summarySentences, rawSentences) {
    this.summaryContainer.innerHTML = "";  // reset the container
    this.summaryIDToContainer = {};
        
    for (let sentenceID of summarySentences) {
      
      let outer = document.createElement("div");
      outer.classList.add("card");
      outer.classList.add("candidate-card");
      this.candidateIDToContainer[sentenceID] = outer;
      
      // allow drag
      outer.draggable = true;
      outer.addEventListener("dragstart", ev => {ev.dataTransfer.setData("text/plain", `${sentenceID}`)});
      
      // TODO: implement selection
      outer.addEventListener("click", function(){console.log("clicked: ", sentenceID)}, true);

      let inner = document.createElement("div");
      inner.classList.add("card-body");

      let text = document.createTextNode(rawSentences[sentenceID]);

      // Assemble!
      this.summaryContainer.appendChild(outer);
      outer.appendChild(inner);
      inner.appendChild(text);
    }
  }
  
  // TODO: add stuff to render everything else :D 
}



