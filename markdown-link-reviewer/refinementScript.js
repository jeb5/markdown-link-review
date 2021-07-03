let getFormData = form => Array.from(new FormData(form)).reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

let getfirstCN = className => document.getElementsByClassName(className)[0];

const form = getfirstCN("form");
const judgeEls = Array.from(document.getElementsByClassName("judgeEl"));
const formEls = {
	progressHeading: getfirstCN("boxProgressHeading"),
	linkNameInfo: getfirstCN("linkNameInfo"),
	urlInfo: getfirstCN("urlInfo"),
	problemIdentifiedInfo: getfirstCN("problemIdentifiedInfo"),
	updatedProblemField: document.getElementById("updatedProblemField"),
	replacementUrlField: document.getElementById("replacementUrlField"),
	noteField: document.getElementById("noteField"),
};

form.addEventListener("change", updateDisabledness);
function updateDisabledness() {
	formData = getFormData(form);
	if (formData.judgement === "working") {
		judgeEls.forEach(el => {
			el.disabled = true;
			el.classList.add("disabled");
		});
	} else if (formData.judgement === "broken") {
		judgeEls.forEach(el => {
			el.disabled = false;
			el.classList.remove("disabled");
		});
	}
}
getfirstCN("backBtn").addEventListener("click", e => {
	if (currentIndex > 0) setNewIndex(currentIndex - 1);
});
getfirstCN("fowardBtn").addEventListener("click", e => {
	if (currentIndex < linkIds.length - 1) setNewIndex(currentIndex + 1);
});
function setNewIndex(index) {
	currentIndex = index;
	form.classList.add("disabled");
	socket.send(JSON.stringify({ type: "startLink", data: { id: linkIds[currentIndex] } }));
}

let linkIds = [];
let currentIndex = 0;

let socket = new WebSocket("ws://localhost:8006");
socket.onmessage = function (event) {
	msgDict = JSON.parse(event.data);
	msgType = msgDict.type;
	msgData = msgDict.data;
	console.log("Message from WS", msgDict);
	switch (msgType) {
		case "hello":
			//msgData is list of ids
			linkIds = msgData;
			setNewIndex(0);
			return;
		case "link":
			//msgData is link details
			form.classList.remove("disabled");
			return setData(msgData);
		case "linkUpdated":
			//confirmation that link was updated. msgData is link id.
			if (currentIndex < linkIds.length - 1) {
				setNewIndex(currentIndex + 1);
			} else {
				socket.send(JSON.stringify({ type: "endJudgement" }));
			}
	}
};

// let currentData = {};
function setData(newData) {
	currentData = newData;
	form.reset();
	if (!newData) return;
	formEls.progressHeading.innerText = `Link ${currentIndex + 1} of ${linkIds.length}`;
	formEls.linkNameInfo.innerText = newData.name;
	formEls.urlInfo.innerText = newData.url;
	formEls.problemIdentifiedInfo.innerText = newData.problem;
	formEls.updatedProblemField.innerText = newData.problem;
	updateDisabledness();
}

function getNiceFormData() {
	//returns just the data from the form
	let formData = getFormData(form);
	console.log(formData);
	let formValid = formData.judgement === "working";
	return {
		isValid: formValid,
		problem: !formValid ? formData.updatedProblemField : "",
		replacement: !formValid ? formData.replacementUrlField : "",
		note: formData.noteField,
	};
}

form.addEventListener("submit", e => {
	e.preventDefault();
	if (form.classList.contains("disabled")) return;
	formData = getNiceFormData();
	console.log("submitting form data:", formData);
	message = {
		type: "updateLink",
		data: { id: linkIds[currentIndex], ...getNiceFormData() },
	};
	form.classList.add("disabled");
	socket.send(JSON.stringify(message));
});
