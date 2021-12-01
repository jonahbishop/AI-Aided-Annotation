import {DEMO_ARTICLE_SENTENCES} from "./demo_article.js";
import {uploadDocument, rank} from "./api.js";


let uploadClickHandler = function() {
  
  let rawdoc = document.getElementById("rawdoctextarea").value;

  let uploadSuccessFn = function(res) {
    res = JSON.parse(res);
    document.getElementById("upload-results-json").innerHTML = JSON.stringify(res, null, 2);
    if (res['session_id']) {
      document.getElementById("session-id").value = res['session_id'];
    }
  };
  
  let uploadErrorFn = function(res) {
    document.getElementById("upload-results-error").innerHTML = res;
  };
  
  uploadDocument(rawdoc, uploadSuccessFn, uploadErrorFn);
};


let rankHandler = function() {
  
  
  let sessionId = document.getElementById("session-id").value;
  
  let keywords = document.getElementById("keywords").value.split(', ');
  
  let rawSummary = document.getElementById("summary").value;
  let summary = rawSummary === '' ? [] : rawSummary.split(' ').map(x=>parseInt(x));
  
  
  console.log(sessionId, keywords, summary);
  
  let rankSuccessFn = function(res) {
    document.getElementById("rank-results-json").innerHTML = JSON.stringify(JSON.parse(res), null, 2);
  };
  
  let rankErrorFn = function(res) {
    document.getElementById("rank-results-error").innerHTML = res;
  };
  
  rank(sessionId, keywords, summary, rankSuccessFn, rankErrorFn);
  
}






window.onload = function() {
  // Pre-fill the text area w/ a document, for convenience.
  document.getElementById("rawdoctextarea").value = DEMO_ARTICLE_SENTENCES.join(' ');
  
  document.getElementById("upload-button").addEventListener("click", uploadClickHandler);
  
  document.getElementById("rank-button").addEventListener("click", rankHandler);
  
  
  // Simulate an "upload" click, for convenience.
  uploadClickHandler();
  
  
    
};
