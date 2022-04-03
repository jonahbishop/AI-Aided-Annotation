// The "View" class handles how to render stuff to the page.

export class View {
    constructor(rawDocumentContainer, candidatesContainer, summaryContainer, keywordsContainer) {
        this.rawDocumentContainer = rawDocumentContainer;
        this.candidatesContainer = candidatesContainer;
        this.summaryContainer = summaryContainer;

        this.keywordsContainer = keywordsContainer; // NOTE: this might be handled differently w/ that library

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


    // minScore and maxScore are the min and max scores for all the candidates
    makeScoreVisualization(lscore, rscore, score, minScore, maxScore, lambda) {

        let row = document.createElement("div");
        row.classList.add("row");
        let container = document.createElement("div");
        container.classList.add("col-12");

        // To get the line to cover more space, we scale based on this value.
        // Without this, if the maximum score was 0.01, our visualization would be a tiny, tiny sliver of a line. :)
        let m = 1 / Math.max(-minScore, maxScore);
        // let daMaxLol = Math.max(-minScore, maxScore);

        // OKAY:
        // we essentially want a green bar going from 0 to 'score', and then a red bar going from 'score' to 'lscore' (i.e. the max score)
        // BUT: things get weird if score < 0 :)
        // In that case, we don't need a green bar at all, and we want a red bar from 'score' to 'lscore'.
        // If it's easier, we can just draw a green box that gets clobbered by the red :)

        let zeroPoint = 125;
        let scorePoint = 125 + 100 * score * m;
        let maxScorePoint = 125 + 100 * lscore * m;

        let greenRectX = zeroPoint;
        let greenRectW = scorePoint - zeroPoint;

        let redRectX = scorePoint;
        let redRectW = maxScorePoint - scorePoint;

        let prettyScore = Math.round(score * 100) / 100;
        let minScorePoint = 125 + 100 * (lscore - rscore) * m;

        let greenRectHTML = `<rect x="${greenRectX}" y="12" rx="1" ry="1" width="${greenRectW}" height="6"
            style="fill:green;opacity:0.5" />`;

        container.innerHTML = `
    <svg width="256px" height="40px">
    
      ${score > 0 ? greenRectHTML : ''}
                  
      <rect x="${redRectX}" y="12" rx="1" ry="1" width="${redRectW}" height="6"
            style="fill:red;opacity:0.5" />
            
        <line x1="${scorePoint}" y1="7" x2="${scorePoint}" y2="23" style="stroke:rgb(140,140,140);stroke-width:1" />
        <text x="${scorePoint}" y="33" font-size="10px" fill="grey">${prettyScore}</text>
        
        <line x1="${minScorePoint}" y1="7" x2="${minScorePoint}" y2="23" style="stroke:rgb(200, 20, 20);stroke-width:1" />
    </svg>
    `;

        row.appendChild(container);
        return row;

    }

    // This is the version where lambda=0 has meaning
    makeAlternateScoreVisualization(lscore, rscore, score, minScore, maxScore, lambda) {

        let row = document.createElement("div");
        row.classList.add("row");
        let container = document.createElement("div");
        container.classList.add("col-12");

        // To get the line to cover more space, we scale based on this value.
        // Without this, if the maximum score was 0.01, our visualization would be a tiny, tiny sliver of a line. :)
        let m = 1 / Math.max(-minScore, maxScore);

        // What we want:
        // dark green bar going from this -rscore to score
        // light-green bar going from score to lscore.

        let lowScoreX = 125 - 100 * rscore * m;
        let scoreX = 125 + 100 * score * m;
        let highScoreX = 125 + 100 * lscore * m;

        let prettyScore = Math.round(score * 1000) / 1000;

        container.innerHTML = `
    <svg width="256px" height="40px">
    
      <rect x="${lowScoreX}" y="12" rx="1" ry="1" width="${scoreX-lowScoreX}" height="6"
            style="opacity:0.7" />
            
      <rect x="${scoreX}" y="12" rx="1" ry="1" width="${highScoreX-scoreX}" height="6"
            style="opacity:0.3" />
            
        <line x1="${scoreX}" y1="7" x2="${scoreX}" y2="23" style="stroke:rgb(140,140,140);stroke-width:1" />
        <text x="${scoreX}" y="33" font-size="10px" fill="grey">${prettyScore}</text>
        
        <line x1="125" y1="2" x2="125" y2 = "28" style="stroke:grey;stroke-width:1" stroke-dasharray="2 1" />
        
    </svg>
    `;

        row.appendChild(container);
        return row;

    }

    // gonna be haaaaacky
    wrapKeywordsInSentence(sentence, kws) {
        let isKeyword = (word) => {
            let w = word.replace(/[^a-z]/gi, '');
            w = w.toLowerCase();
            if (kws.includes(w)) return true;
            // maybe it's plural? lol. haaaaacky.
            if (w[w.length - 1] === 's' && kws.includes(w.substring(0, w.length - 1))) return true;
            return false;
        };

        return sentence.split(' ').map(word => {
            if (!isKeyword(word)) {
                return word;
            } else {
                return `<span class="kw-rank">${word}</span>`;
            }
        }).join(' ');
    }



    // TODO: complete this function. Document what 'candidates' is :)
    renderCandidates(candidates, lambda, rawSentences, keywords, useV2) {
        // candidates is a list: [{ID, lscore, rscore, score, rank, prev_rank}, ...]

        console.log("Using v2? ", useV2);

        this.candidatesContainer.innerHTML = ""; // reset the container
        this.candidateIDToContainer = {};

        // We need these later on, but we only need to calculate them once, so we do it outside of the loop.
        let maxScore = Math.max(...candidates.map(x => x.lscore));
        let minScoreV1 = Math.min(...candidates.map(x => x.lscore - x.rscore));
        let minScoreV2 = Math.min(...candidates.map(x => -x.rscore));
        // 
        for (let candidate of candidates.slice(0, 25)) {

            let outer = document.createElement("div");
            outer.classList.add("card");
            outer.classList.add("candidate-card");
            outer.id = "candidate-" + candidate.ID;
            this.candidateIDToContainer[candidate.ID] = outer;

            // allow drag
            outer.draggable = true;
            outer.addEventListener("dragstart", ev => { ev.dataTransfer.setData("text/plain", `${candidate.ID}`) });

            // TODO: implement selection :D
            outer.addEventListener("click", function() { console.log("clicked: ", candidate.ID) }, true);

            let cardBody = document.createElement("div");
            cardBody.classList.add("card-body");

            let row = document.createElement("div");
            row.classList.add("row");

            let sentenceCol = document.createElement("div");
            sentenceCol.classList.add("col-10");

            let rankChangeCol = document.createElement("div");
            rankChangeCol.classList.add("col-2");

            let sentenceHTML = this.wrapKeywordsInSentence(rawSentences[candidate.ID], keywords);

            let [r, prevR] = [candidate.rank, candidate.prev_rank];
            let rankChange = "";
            if (r && prevR && r !== prevR) {
                let delta = prevR - r;
                rankChange = `${delta > 0 ? '+' : ''}${delta}`;
            }
            rankChange = document.createTextNode(rankChange);


            let scoreViz = (
                useV2 ?
                this.makeAlternateScoreVisualization(candidate.lscore, candidate.rscore, candidate.score, minScoreV2, maxScore, lambda) :
                this.makeScoreVisualization(candidate.lscore, candidate.rscore, candidate.score, minScoreV1, maxScore, lambda)
            );


            // TODO: add a visualization of the score!!!

            // Assemble!
            // Note: It'd be clearer if we just set innerHTML... 
            this.candidatesContainer.appendChild(outer);
            outer.appendChild(cardBody);
            cardBody.appendChild(row);
            row.appendChild(sentenceCol);
            sentenceCol.innerHTML = sentenceHTML;
            // sentenceCol.appendChild(sentenceText);
            row.appendChild(rankChangeCol);
            rankChangeCol.appendChild(rankChange);
            cardBody.appendChild(scoreViz);
        }
    }

    resetSummary() {
        this.summaryContainer.innerHTML = `<div class="p-2 summary-default">Drag sentences here to create your summary. </div>`;
    }

    resetSummaryToNothing() {
        this.summaryContainer.innerHTML = ``;
    }

    // summarySentences: List[IDs]
    // rawSentences: List[Text]  (index is ID)
    renderSummary(summarySentences, rawSentences) {
        this.summaryContainer.innerHTML = ""; // reset the container
        this.summaryIDToContainer = {};

        for (let sentenceID of summarySentences) {

            let outer = document.createElement("div");
            outer.classList.add("card");
            outer.classList.add("candidate-card");
            this.candidateIDToContainer[sentenceID] = outer;

            // allow drag
            outer.draggable = true;
            outer.addEventListener("dragstart", ev => { ev.dataTransfer.setData("text/plain", `${sentenceID}`) });

            // TODO: implement selection
            outer.addEventListener("click", function() { console.log("clicked: ", sentenceID) }, true);

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