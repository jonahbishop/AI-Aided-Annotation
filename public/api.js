export function uploadDocument(doc, cb, errorCb) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    cb = cb || function(res) { console.log("Result: ", res); };
    errorCb = errorCb || function(res) { console.log("Error: ", res); };

    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return;

        // console.log("Response from '/upload' request:\n", xhr.response);

        if (xhr.status == 200) {
            cb(xhr.responseText);
        } else {
            errorCb(xhr.responseText);
        }
    };

    let payload = JSON.stringify({
        rawdocument: doc,
    });

    // console.log("Sending the following to the /upload endpoint: ", payload);
    xhr.send(payload);

}

export function rank(sessionId, keywords, summary, cb, errorCb) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/rank", true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    cb = cb || function(res) { console.log("Result: ", res); };
    errorCb = errorCb || function(res) { console.log("Error: ", res); };

    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return;

        // console.log("Response from '/rank' request:\n", xhr.response);

        if (xhr.status == 200) {
            cb(xhr.responseText);
        } else {
            errorCb(xhr.responseText);
        }
    };

    let payload = JSON.stringify({
        session_id: sessionId,
        keywords: keywords,
        summary: summary
    });
    // console.log("Sending the following to the '/rank' endpoint:\n", JSON.parse(payload));
    // console.log(payload);
    xhr.send(payload);

}

export function phase_two(sessionId, summary, cb, errorCb) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/phase_two", true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    cb = cb || function(res) { console.log("Result: ", res); };
    errorCb = errorCb || function(res) { console.log("Error: ", res); };

    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 3) return;

        // console.log("Response from '/rank' request:\n", xhr.response);

        if (xhr.status == 200) {
            cb(xhr.responseText);
        } else {
            errorCb(xhr.responseText);
        }
    };

    let payload = JSON.stringify({
        session_id: sessionId,
        top_sentences: summary
    });
    // console.log("Sending the following to the '/rank' endpoint:\n", JSON.parse(payload));
    // console.log(payload);
    xhr.send(payload);

}