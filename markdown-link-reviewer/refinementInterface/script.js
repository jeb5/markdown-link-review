const updateNeedRemoveDisable = checked =>
	Array.from(document.getElementsByClassName("fix")).forEach(
		checked ? el => el.classList.add("disabled2") : el => el.classList.remove("disabled2")
	);
document.getElementById("needRemoveCheck").addEventListener("change", e => updateNeedRemoveDisable(e.target.checked));
const updateBrokenDisable = checked =>
	Array.from(document.getElementsByClassName("judge")).forEach(
		checked ? el => el.classList.remove("disabled1") : el => el.classList.add("disabled1")
	);
document.getElementById("brokenCheck").addEventListener("change", e => updateBrokenDisable(e.target.checked));
const updateFormDisable = disabled =>
	Array.from(document.getElementById("form").children).forEach(
		disabled ? el => el.classList.add("disabled3") : el => el.classList.remove("disabled3")
	);

const infoEls = {
	heading: document.getElementById("boxProgressHeading"),
	name: document.getElementById("nameInfo"),
	url: document.getElementById("urlInfo"),
	problem: document.getElementById("problemInfo"),
	replacementUrl: document.getElementById("replacementUrlSuggestInfo"),
};
const formEls = {
	broken: document.getElementById("brokenCheck"),
	problem: document.getElementById("problemField"),
	needRemove: document.getElementById("needRemoveCheck"),
	replacementName: document.getElementById("replacementNameField"),
	replacementUrl: document.getElementById("replacementUrlField"),
	note: document.getElementById("noteField"),
};

/* 
formData = {
	info: {
		index,
		total,
		name,
		url,
	},
	bot: {
		problem,
		replacementUrl,
	},
	human: {
		broken,
		problem,
		needRemove,
		replacementUrl,
		replacementName,
		note,
	}
}
*/
const resetForm = () => setForm({});
const setForm = formData => {
	const {
		info = { name: "...", url: "..." },
		extra = { index: "?", total: "?" },
		bot = { problem: "...", replacementUrl: "..." },
		human = { broken: true, problem: "", needRemove: false, replacementUrl: "", replacementName: "", note: "" },
	} = formData;
	infoEls.heading.innerText = `Link ${extra.index} of ${extra.total}`;
	infoEls.name.innerText = info.name;
	infoEls.url.innerText = info.url;
	infoEls.problem.innerText = bot.problem;
	infoEls.replacementUrl.innerText = bot.replacementUrl;
	formEls.broken.checked = human.broken;
	updateBrokenDisable(human.broken);
	formEls.problem.value = human.problem;
	formEls.needRemove.checked = human.needRemove;
	updateNeedRemoveDisable(human.needRemove);
	formEls.replacementUrl.value = human.replacementUrl;
	formEls.replacementUrl.placeholder = info.url;
	formEls.replacementName.value = human.replacementName;
	formEls.replacementName.placeholder = info.name;
	formEls.note.value = human.note;
};

//returns the "form" part of the form
const getForm = () => ({
	broken: formEls.broken.checked,
	problem: formEls.problem.value,
	needRemove: formEls.needRemove.checked,
	replacementUrl: formEls.replacementUrl.value,
	replacementName: formEls.replacementName.value,
	note: formEls.note.value,
});

formEl = document.getElementById("form");

formEl.addEventListener("submit", e => {
	e.preventDefault();
	console.log("Form submitted");
	submitLink();
});

document.getElementById("backBtn").addEventListener("click", e => {
	startLinkWithIndex(linkIndex - 1);
});
document.getElementById("fowardBtn").addEventListener("click", e => {
	startLinkWithIndex(linkIndex + 1);
});

updateFormDisable(true);
resetForm();

let linkIds = [];
let links = {}; //contains a cached copy of link details, with ids as keys
let linkIndex = -1;
let requestingLink = false;

function requestLink(index) {
	linkIndex = index;
	linkId = linkIds[index];
	if (!linkId) {
		alert("All links have been judged");
		return;
	}
	link = links[linkId];
	updateFormDisable(true);
	socket.send(JSON.stringify({ type: "startLink", data: { id: linkId } }));
	setForm({ index: linkIndex + 1, total: linkIds.length, ...link });
	requestingLink = linkId;
}
function recieveLink(linkObj) {
	if (requestingLink != linkObj._id) return;
	const { human, bot } = linkObj;
	link = {
		judged: false,
		info: {
			name: linkObj.name,
			url: linkObj.url,
		},
		bot: {
			problem: bot.problem,
			replacementUrl: bot.urlUpdate,
		},
		human: {
			broken: human.broken,
			problem: human.problem,
			replacementUrl: human.urlUpdate,
			replacementName: human.nameUpdate,
			needRemove: human.needRemove,
			note: human.note,
		},
	};
	links[linkIndex] = link;
	setForm({ extra: { index: linkIndex + 1, total: linkIds.length }, ...link });
	updateFormDisable(false);
	requestingLink = false;
}
function startLinkWithIndex(index) {
	if (index >= linkIds.length || index < 0) return false;
	requestLink(index);
}
function nextLink() {
	let newIndex = linkIndex + 1;
	if (newIndex >= linkIds.length) {
		newIndex = linkIds.findIndex(el => Object.keys(links[el]).length == 0 || links[el].judged == false);
		if (newIndex == -1) {
			if (window.confirm("All links have been judged. Finish refinement?")) {
				socket.send(JSON.stringify({ type: "endJudgement" }));
				window.close();
			}
			return;
		}
	}
	requestLink(newIndex);
}
function submitLink() {
	const linkId = linkIds[linkIndex];
	const judgement = { id: linkId, ...getForm() };
	links[linkId].judged = true;
	socket.send(JSON.stringify({ type: "updateLink", data: judgement }));
	updateFormDisable(true);
}

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
			linkIds.forEach(id => {
				links[id] = {};
			});
			requestLink(0);
			return;
		case "link":
			//msgData is link details
			recieveLink(msgData);
			return;
		case "linkUpdated":
			//confirmation that link was updated. msgData is link id.
			if (msgData == linkIds[linkIndex]) {
				nextLink();
			}
	}
};
