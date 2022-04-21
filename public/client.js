import { DEMO_ARTICLE_TEXT, DEMO_journal_article, DEMO_Legal_Reputation } from "./demo_article.js";
import { uploadChapter, rank, phase_two } from "./api.js";
import { View } from "./view.js";
const SlimSelect = window.SlimSelect;


let view;

// These change when a user uploads a new document
let rawSentences = []; // List: ID->sentence
let rawChapter = "";
let keywords = []; // might not need this?
let sessionID = null;

// These are involved in the ranking.
let candidateSentences = []; // list: [{ID, lscore, rscore, score, rank, prev_rank}, ...]
let summarySentences = []; // [IDs]
let lambda = 0.15; // set the value of lambda here

// Information about sentence selection
let numAutoSentences = getNumAutoSentences(); // ID?

// calculate the final MMR score
function mmrScore(sim1, sim2, lambda) {
    return lambda * sim1 - (1 - lambda) * sim2;
}

function getNumAutoSentences() {
    let autoPopulateSlider = document.getElementById("autoPopulateSlider");
    // Note: the slider is an int from 0 to 100, but we want a float from 0 to 1.
    return autoPopulateSlider.valueAsNumber;
}

function handleAutoSliderChange() {

    numAutoSentences = getNumAutoSentences();
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
    initiateRerank(); // Need to rerank now that we have a new summary sentence
}

// Moving a sentence from summary -> candidates
function onDropInCandidatesSection(ev) {
    ev.preventDefault();
    let sentenceID = parseInt(ev.dataTransfer.getData("text/plain"));

    if (!summarySentences.includes(sentenceID)) return;

    summarySentences = summarySentences.filter(id => id != sentenceID);
    candidateSentences.push({ ID: sentenceID });

    view.renderSummary(summarySentences, rawSentences);
    initiateRerank(); // Need to rerank now that the summary sentences have changed.
}

let autoPopulateHandler = function() {

    console.log("Auto Populate Pressed")

    // discard current summary
    view.resetSummaryToNothing();

    console.log("There will be " + numAutoSentences + " sentences in summary as a result of auto populate");

    for (let i = 0; i < numAutoSentences; i++) {

        const sentenceID = candidateSentences[0].ID;
        console.log(sentenceID)

        document.getElementById('summary-view').appendChild(document.getElementById('ranking-view').firstChild);
        document.getElementById('ranking-view').firstChild.remove;

        let newCandidates = candidateSentences.filter(c => (c.ID != sentenceID));
        if (newCandidates.length === candidateSentences.length) return; // Wasn't a candidate sentence

        summarySentences.push(sentenceID);
        candidateSentences = newCandidates;

        // We need to redraw the summary and rerank :)
        view.renderSummary(summarySentences, rawSentences);
        initiateRerank(); // Need to rerank now that we have a new summary sentence
    }
}

let nextHandler = function() {

    console.log("Next Pressed")

    if (sessionID === null) {
        alert("Please upload a document first!");
        return;
    }

    phase_two(sessionID, summarySentences, handleSimResults);

    const element = document.getElementById("scroll-here");
    element.scrollIntoView()
}

let newQuestionHandler = function() {

    console.log("New Question Pressed")

    if (sessionID === null) {
        alert("Please upload a document first!");
        return;
    }

    view.renderNewQuestion()
}

let exportHandler = function() {

    console.log("Export Pressed")

    if (sessionID === null) {
        alert("Please upload a document first!");
        return;
    }

    // get the generated summary text
    let genSumCol = document.getElementsByClassName("gen-sum-body")
    let genSumText = "";
    for (const item of genSumCol) {
        genSumText += item.innerText;
    }

    // get the keywords
    let keywords = document.getElementsByClassName("keywords-body")
    let keywordsText = "";
    for (const item of keywords) {
        keywordsText += item.innerText;
    }

    // get the questions and answers
    const questions = document.getElementsByClassName("question")
    const answers = document.getElementsByClassName("answer")
    let questionsAndAnswers = {}
    for (let i = 0; i < questions.length; i++) {
        questionsAndAnswers[questions[i].value] = answers[i].value
    }

    // put it all together
    let dict = { "summary": genSumText, "keywords": keywordsText, "questionsAndAnswers": questionsAndAnswers }
    let jsonData = JSON.stringify(dict)
    download(jsonData, 'rich_data.json', 'application/json');
}

function download(content, fileName, contentType) {
    var a = document.createElement("a");
    var file = new Blob([content], { type: contentType });
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
}

let handleSimResults = function(res) {


    res = JSON.parse(res);

    //console.log(res.similar_sentences)
    //console.log(res.keywords)

    view.renderGeneratedSummary(summarySentences, rawSentences, res.similar_sentences, res.keywords.slice(0, 5));
}


/////////////////////////////////
// Functions dealing w/ ranking
/////////////////////////////////

// This is called when we get back ranking results from the backend.
function handleRerankResult(res) {
    res = JSON.parse(res);
    // console.log(Object.values(res));

    if (candidateSentences.length < 1) {
        // i.e. we haven 't clicked "rank" yet for this document, and all the sentences are candidates with no previous scores. 
        candidateSentences = rawSentences.map((s, idx) => ({ ID: idx }));
    }

    let idToPreviousRank = new Map(candidateSentences.map(c => [c.ID, c.rank]));

    candidateSentences = Object.values(res).map(s => ({
        // candidateSentences = res["sen_scores"].map(s => ({
        ID: parseInt(s.sentID),
        lscore: s.lscore,
        rscore: s.rscore,
        score: mmrScore(s.lscore, s.rscore, lambda),
        prev_rank: idToPreviousRank.get(parseInt(s.sentID)),
    }));
    candidateSentences.sort((c1, c2) => (c1.score < c2.score ? 1 : (c1.score > c2.score ? -1 : 0)));
    candidateSentences = candidateSentences.map((candidate, idx) => {
        candidate["rank"] = idx + 1;
        return candidate;
    });

    // console.log("Candidates before rendering: ", candidateSentences);

    view.renderCandidates(candidateSentences, rawSentences, query_slimSelect.selected());
}

// Ping the backend to get a new ranking.
function initiateRerank() {

    if (sessionID === null) {
        alert("Please upload a document first!");
        return;
    }
    console.log("reranking");
    rank(sessionID, query_slimSelect.selected(), summarySentences, handleRerankResult);
}

function onKeywordsChange() {
    if (candidateSentences.length < 1) return;
    initiateRerank();
}




/////////////////////////////////
// Upload function
/////////////////////////////////

var query_slimSelect = new SlimSelect({
    select: '#query',
    hideSelectedOption: true,
});

window.sselect = query_slimSelect; // for debugging :)

let uploadClickHandler = function() {
    let rawchap = document.getElementById("rawdoctextarea").value;

    // save the sessionID
    let uploadSuccessFn = function(res) {
        res = JSON.parse(res);

        // Set global variables.
        sessionID = res["session_id"];
        rawSentences = res["sentences"].map(s => s[0]);
        keywords = res["keywords"]; // TODO: possibly map
        rawChapter = rawchap;

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
            let gr = ((keywords_len - idx) * 255 / keywords_len).toString();
            let rd = ((idx) * 255 / keywords_len).toString();
            console.log(s);
            curr_obj.text = `${s[0]} (${s[1]})`;
            curr_obj.innerHTML = "<div>" + s[0] + "</div>" + '<div style="color:rgb(' + rd + ' ,' + gr + ' ,' + bl + ' );">(' + s[1] + ')</div>';
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
        view.renderRawChapter(rawChapter, rawSentences);
        // discard current summary
        view.resetSummary();

        // Maybe we just rank then?
        initiateRerank();
    };

    let uploadErrorFn = function(res) {
        document.getElementById("upload-results-error").innerHTML = res;
    };

    uploadChapter(rawchap, uploadSuccessFn, uploadErrorFn);
    document.getElementById("btn-modal-close").click();

};

// Any initialization code that accesses HTML elements in the document should
// go here. This will be called once the page is fully loaded.
window.onload = function() {
    // Click the upload button on startup
    document.getElementById("upload-button").click();

    for (let [id, txt] of[["demo-1", DEMO_ARTICLE_TEXT], ["demo-2", DEMO_journal_article], ["demo-3", DEMO_Legal_Reputation]]) {
        document.getElementById(id).onclick = () => {
            document.getElementById("rawdoctextarea").value = txt;
        };
    }

    view = new View(
        document.getElementById("chapter-view"),
        document.getElementById("ranking-view"),
        document.getElementById("summary-view"),
        document.getElementById("generated-summary-view"),
        document.getElementById("data-view"));

    let autoPopulateSlider = document.getElementById("autoPopulateSlider");
    autoPopulateSlider.onchange = handleAutoSliderChange;

    let uploadButtonModal = document.getElementById("upload_button_modal");
    uploadButtonModal.onclick = uploadClickHandler;

    let autoPopulateButton = document.getElementById("auto-populate-button");
    autoPopulateButton.onclick = autoPopulateHandler;

    let nextButton = document.getElementById("next-button");
    nextButton.onclick = nextHandler;

    let newQuestionButton = document.getElementById("new-question-button");
    newQuestionButton.onclick = newQuestionHandler;

    let exportButton = document.getElementById("export-button");
    exportButton.onclick = exportHandler;

    document.getElementById("summary-view").ondragover = (ev => ev.preventDefault());
    document.getElementById("summary-view").ondrop = onDropInSummarySection;

    document.getElementById("ranking-view").ondragover = (ev => ev.preventDefault());
    document.getElementById("ranking-view").ondrop = onDropInCandidatesSection;

    query_slimSelect.onChange = onKeywordsChange;
};

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