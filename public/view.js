// The "View" class handles how to render stuff to the page.

export class View {
    constructor(rawChapterContainer, candidatesContainer, summaryContainer, generatedSummaryContainer, dataContainer) {
        this.rawChapterContainer = rawChapterContainer;
        this.candidatesContainer = candidatesContainer;
        this.summaryContainer = summaryContainer;
        this.generatedSummaryContainer = generatedSummaryContainer;
        this.dataContainer = dataContainer;

        // TODO: add mappings from sentence ID -> div/span/etc. so that we can easily "select" or "deselect" a sentence, or otherwise
        // highlight it. These can be populated whenever we call renderCandidates, renderRawDocuemnt, and renderSummary.
        this.candidateIDToContainer = {};
    }

    renderRawChapter(rawChapter, sentences) {

        this.rawChapterContainer.innerHTML = "";

        console.log("INCLUDES TEST: ");
        for (let s of sentences) {
            if (!rawChapter.includes(s)) {
                console.log(s);
            }
        }


        // This is very not robust :)
        for (let paragraph of rawChapter.split("\n\n")) {
            let p = document.createElement("p");
            let txt = document.createTextNode(paragraph);

            this.rawChapterContainer.append(p);
            p.append(txt);
        }
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
    renderCandidates(candidates, rawSentences, keywords) {
        // candidates is a list: [{ID, lscore, rscore, score, rank, prev_rank}, ...]

        this.candidatesContainer.innerHTML = ""; // reset the container
        this.candidateIDToContainer = {};

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

            let sentenceHTML = this.wrapKeywordsInSentence(rawSentences[candidate.ID], keywords);

            let [r, prevR] = [candidate.rank, candidate.prev_rank];
            let rankChange = "";
            if (r && prevR && r !== prevR) {
                let delta = prevR - r;
                rankChange = `${delta > 0 ? '+' : ''}${delta}`;
            }

            // Assemble!
            this.candidatesContainer.appendChild(outer);
            outer.appendChild(cardBody);
            cardBody.appendChild(row);
            row.appendChild(sentenceCol);
            sentenceCol.innerHTML = sentenceHTML;
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
            inner.innerHTML = rawSentences[sentenceID];

            // Assemble!
            this.summaryContainer.appendChild(outer);
            outer.appendChild(inner);
        }
    }

    // summarySentences: List[IDs]
    // rawSentences: List[Text]  (index is ID)
    renderGeneratedSummary(summarySentences, rawSentences, similarSentences, keywords) {
        this.generatedSummaryContainer.innerHTML = ""; // reset the container
        this.dataContainer.innerHTML = ""; // reset the container

        let keyword = []
        for (let i = 0; i < keywords.length; i++) {
            keyword.push(keywords[i][0])
        }

        console.log(keyword)

        // iterate over the selected diverse sentences
        for (let sentenceID of summarySentences) {

            let outer = document.createElement("div");
            outer.classList.add("card");
            outer.classList.add("candidate-card");
            this.candidateIDToContainer[sentenceID] = outer;

            let inner = document.createElement("div");
            inner.classList.add("gen-sum-body");

            // add the diverse sentence and all the similar ones to a textNode
            let textPlusSum = `<span class="ds-rank">${rawSentences[sentenceID]}</span>`;
            for (let simSentence of similarSentences[sentenceID]) {
                textPlusSum += this.wrapKeywordsInSentence(rawSentences[simSentence], keyword);
            }

            // Assemble!
            this.generatedSummaryContainer.appendChild(outer);
            outer.appendChild(inner);
            inner.innerHTML = textPlusSum;
        }

        // add the keyword box for the annotated data column
        // TODO: Get the keywords from the sentences
        let keywordBox = document.createElement("div");
        keywordBox.classList.add("card");
        keywordBox.classList.add("data-card");

        let innerKeywordBox = document.createElement("div");
        innerKeywordBox.classList.add("card-body");
        innerKeywordBox.classList.add("keywords-body");
        innerKeywordBox.innerHTML = keyword

        this.dataContainer.appendChild(keywordBox);
        keywordBox.appendChild(innerKeywordBox);
    }

    renderNewQuestion() {
        let outer = document.createElement("div");
        outer.classList.add("card");
        outer.classList.add("q&a-card");
        outer.classList.add("p-1");

        let question = document.createElement("textarea");
        question.classList.add("question");
        question.classList.add("p-1");
        question.classList.add("card-body");
        question.placeholder = "Type Question Here"

        let answer = document.createElement("textarea");
        answer.classList.add("answer");
        question.classList.add("card-body");
        answer.classList.add("p-1");
        answer.placeholder = "Type Answer Here"

        // Assemble!
        this.dataContainer.appendChild(outer);
        outer.appendChild(question);
        outer.appendChild(answer);
    }
}