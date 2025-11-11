var questions = [{"Type": "Type I (Element verification)", "ID": "I_0", "Question": "Does the 'Coffee Shop' area contain the following: 'Seating Area', 'Service Area', 'Customer Waiting Area'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other"}, {"Type": "Type I (Element verification)", "ID": "I_1", "Question": "Does the 'Seating Area' area contain the following: 'Table', 'Chair'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other"}, {"Type": "Type I (Element verification)", "ID": "I_2", "Question": "Does the 'Service Area' area contain the following: 'Counter', 'Pastry Case'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other"}, {"Type": "Type I (Element verification)", "ID": "I_3", "Question": "Does the 'Counter' area contain the following: 'Espresso Machine', 'Cash Register'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other"}, {"Type": "Type I (Element verification)", "ID": "I_4", "Question": "Does the 'Customer Waiting Area' area contain the following: 'Menu Board', 'Pickup Point'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#It contains more%%Other"}, {"Type": "Type II-A (Relation Check)", "ID": "II_0", "Question": "Is the relationship between 'Table' (subject) and 'Chair' (object): 'near'?", "Answers": "#Yes, it is%%Yes#No, it isn't%%No#Not only near%%Other"}, {"Type": "Type II-A (Relation Check)", "ID": "II_1", "Question": "Is the relationship between 'Service Area' (subject) and 'Customer Waiting Area' (object): 'near'?", "Answers": "#Yes, it is%%Yes#No, it isn't%%No#Not only near%%Other"}, {"Type": "Type II-A (Relation Check)", "ID": "II_2", "Question": "Is the relationship between 'Main Entrance Door' (subject) and 'Coffee Shop' (object): 'near'?", "Answers": "#Yes, it is%%Yes#No, it isn't%%No#Not only near%%Other"}, {"Type": "Type II-A (Non-Relation Check)", "ID": "II_3", "Question": "At the location 'Coffee Shop', it seems that 'Seating Area' and 'Service Area' don't have a fixed spatial relationship (random and inconsistent). Is that correct?", "Answers": "#Correct%%Yes#Not true%%No#Partially correct%%Other"}, {"Type": "Type II-A (Non-Relation Check)", "ID": "II_4", "Question": "At the location 'Coffee Shop', it seems that 'Seating Area' and 'Customer Waiting Area' don't have a fixed spatial relationship (random and inconsistent). Is that correct?", "Answers": "#Correct%%Yes#Not true%%No#Partially correct%%Other"}, {"Type": "Type II-A (Non-Relation Check)", "ID": "II_5", "Question": "At the location 'Service Area', it seems that 'Counter' and 'Pastry Case' don't have a fixed spatial relationship (random and inconsistent). Is that correct?", "Answers": "#Correct%%Yes#Not true%%No#Partially correct%%Other"}, {"Type": "Type II-A (Non-Relation Check)", "ID": "II_6", "Question": "At the location 'Counter', it seems that 'Espresso Machine' and 'Cash Register' don't have a fixed spatial relationship (random and inconsistent). Is that correct?", "Answers": "#Correct%%Yes#Not true%%No#Partially correct%%Other"}, {"Type": "Type II-A (Non-Relation Check)", "ID": "II_7", "Question": "At the location 'Customer Waiting Area', it seems that 'Menu Board' and 'Pickup Point' don't have a fixed spatial relationship (random and inconsistent). Is that correct?", "Answers": "#Correct%%Yes#Not true%%No#Partially correct%%Other"}, {"Type": "Type II-B (Edge: Separation)", "ID": "II_8", "Question": "Does the 'Counter' separate 'Service Area' from 'Seating Area, Customer Waiting Area'? ", "Answers": "#Yes, it does%%Yes#No, it doesn't%%No#Partially correct%%Other"}, {"Type": "Type II-B (Edge: Type Check)", "ID": "II_9", "Question": "For the 'Counter' (which separates 'Service Area' from 'Seating Area, Customer Waiting Area'), is it 'impassable'?", "Answers": "#Yes, it is%%Yes#No, it isn't%%No#Not only impassable%%Other"}, {"Type": "Type III (Path)", "ID": "III_0", "Question": "When you perform the activity 'Buy Coffee' as the 'Customer', after you 'Enter' at the 'Main Entrance Door', you usually 'Check Menu' at the 'Menu Board'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}, {"Type": "Type III (Path)", "ID": "III_1", "Question": "When you perform the activity 'Buy Coffee' as the 'Customer', after you 'Check Menu' at the 'Menu Board', you usually 'Order' at the 'Cash Register'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}, {"Type": "Type III (Path)", "ID": "III_2", "Question": "When you perform the activity 'Buy Coffee' as the 'Customer', after you 'Order' at the 'Cash Register', you usually 'Wait' at the 'Pickup Point'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}, {"Type": "Type III (Path)", "ID": "III_3", "Question": "When you perform the activity 'Buy Coffee' as the 'Customer', after you 'Wait' at the 'Pickup Point', you usually 'Sit' at the 'Seating Area'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}, {"Type": "Type III (Path)", "ID": "III_4", "Question": "When you perform the activity 'Make Coffee' as the 'Staff', after you 'Make Espresso' at the 'Espresso Machine', you usually 'Combine Ingredients' at the 'Counter'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}, {"Type": "Type III (Path)", "ID": "III_5", "Question": "When you perform the activity 'Make Coffee' as the 'Staff', after you 'Combine Ingredients' at the 'Counter', you usually 'Provide Final Drink' at the 'Pickup Point'. Is that correct? ", "Answers": "#Yes, correct%%Yes#No, not true%%No#Partially correct%%Other"}];

var survey = [
    {
        "id": "intro",
        "messages": [
            "Hi! We are researchers currently building a knowledge base.",
            "Please help us by sharing your understanding of <b>[Coffee Shop]</b>.",
            "This brief survey of 5 questions will take approximately 3 minutes to complete, and will help validate common spatial knowledge. ",
            "Please answer <b>without</b> searching the internet. The accuracy of your answer <b>will not</b> affect your compensation. Our goal is to collect the public's understanding of this area. Thank you!",
            "buttons-only:#OK, no problem."
        ],
        "validation": "radio"
    }
];

var survey_qid = -1;
var userid = Date.now().toString(36) + Math.random().toString(36).substr(3, 12);
var url = "./";
var answers = []; // all messsages sent by the user
var survey_answers = {}; // survey answers
var survey_platform = "Prolific";
var answer_count = 0;
var task_completed = false;

var init = function () {
    var dict = parse_query_string();

    if ("userid" in dict) userid = dict["userid"];
    if ("platform" in dict) survey_platform = dict["platform"];

    if ("PROLIFIC_PID" in dict) {
        userid = dict["PROLIFIC_PID"];
        survey_platform = "Prolific";
        completion_code = "TEST_CODE";
    }

    var N = 5;
    // // select N random questions
    // const arr = Array.from({length: questions.length}, (_, i) => i);
    // for (let i = arr.length - 1; i > 0; i--) {
    //     const j = Math.floor(Math.random() * (i + 1));
    //     [arr[i], arr[j]] = [arr[j], arr[i]];
    // }
    var start_id = Math.floor(Math.random() * questions.length);
    if ("START_ID" in dict) start_id = parseInt(dict["START_ID"]);
    var interval = Math.floor(questions.length/N)
    var arr = []
    for (let i = 0 ; i < N ; i ++ ) arr.push( (start_id + i*interval)%questions.length );
    // console.log(start_id, interval, arr)
    for (let i = 0 ; i < N ; i ++ ) {
        survey.push({
            "id": questions[arr[i]].ID,
            "messages": [
                questions[arr[i]].Question,
                "buttons-only:"+questions[arr[i]].Answers
            ],
            "validation": "radio"
        });
    }
    console.log(survey);

    chatbot.talk(survey_next_question());
};


var reply = function (chatbot, message) {
    // this function is used for processing users message and then decide how chatbot should reply.
    // you should use function chatbot.talk(["text1","text2"]) to reply.
    if (task_completed) { chatbot.talk(["😀"]); return; }
    if (survey_validate(message)) {
        var answer = message.includes('%%') ? message.split('%%')[1] : message;
        answers[answer_count] = answer;
        answer_count += 1;
        if (survey[survey_qid].id != undefined) survey_answers[survey[survey_qid].id] = answer;
        if (survey[survey_qid].id == "intro") chatbot.talk(survey_next_question());
        else if (answer == "No" || answer == "Other") {
            survey.splice(survey_qid + 1, 0, { "id": survey[survey_qid].id + "_why", "messages": ["Can you explain why?"] })
            chatbot.talk(survey_next_question());
        }
        else if (survey_qid < survey.length - 1) chatbot.talk(survey_next_question());
        else {
            submit_answer(false);
            chatbot.talk(["Your feedback is valuable to us.", "You have completed the task! Thank you for your participation.", "Please click the [SUBMIT] button below to get your completion code."]);
            task_completed = true;
            document.getElementById("submit").style.display = "block";
            document.getElementById("message").disabled = true;
        }
    }
    else chatbot.talk(survey_repeat_question());
}


var click_times = 0
var show_code = function(showcode) {
    if (!showcode) return;
    chatbot.talk(["Your survey completion code is: <b>"+completion_code+"</b>"]);
    document.getElementById("submit-button").innerHTML = "Survey completion code: <b>"+completion_code+"</b>";
    // document.getElementById("submit").style.cursor = "";
    // document.getElementById("submit").onclick = null;
    if ( survey_platform == "Prolific" ) {
        // window.location.href = "https://app.prolific.co/submissions/complete?cc=" + completion_code;
        window.open("https://app.prolific.co/submissions/complete?cc=" + completion_code, '_blank').focus();
    }
}

var submit_answer = function (showcode = true) {
    click_times += 1;
    if ( click_times > 2 ) show_code();
    var res = {
        userid: userid,
        conversation: chatbot.history,
        answers: survey_answers,
        active_time: TimeMe.getTimeOnCurrentPageInSeconds()
    };
    console.log(res);

    // if ( userid.length > 0 ) {
    //     jQuery.ajax({
    //         url: "XXX",
    //         type: "POST",
    //         crossDomain: true,
    //         data: {data:JSON.stringify(res)},
    //         dataType: "json",
    //         success: show_code(showcode),
    //         error:function(e){}
    //     });
    // }
}


var survey_validate = function (input) {
    var strip = function (text) { return text.toLowerCase().replace(/[\s.,\/#!$%\^&\*;:{}=\-_'"`~()]/g, ""); };
    if (strip(input).length < 1) return false;
    if (survey_qid >= survey.length) return true;
    var q = survey[survey_qid];

    if ("validation" in q) {
        var message = q.messages[q.messages.length - 1];
        var options = message.substring(message.indexOf('#'), message.length).split('#');
        var ans = input.split(';');
        var flag = false;
        options.forEach(function (e) {
            ans.forEach(function (a) {
                if (strip(e) == strip(a)) {
                    flag = true;
                }
            })
        });
        return flag;
    } else return true;
};

var completion_code = "testcode";   // Workers who get the code directly from the source file will be rejected

var survey_question = function (qid) {
    if (qid >= survey.length) return "";
    return survey[qid].messages;
}

var survey_next_question = function () {
    survey_qid += 1;
    return survey_question(survey_qid);
};

var survey_question_by_id = function (id) {
    for (var i = 0; i < survey.length; i++) {
        if (survey[i].id == id) {
            survey_qid = i;
            return survey_question(survey_qid);
        }
    }
    return survey_next_question();
};

var survey_repeat_question = function () {
    return text_unsure.concat(survey[survey_qid].messages);
};

var text_unsure = ["Sorry, I don\'t get it.|Sorry, what do you mean?|Sorry, I don\'t understand.|Can you provide a valid answer?"];
var text_more = ["OK. Can you tell me more?|Uh huh, and?|Good, go ahead.|Well... it will be better if you can tell me more.|Cool, go ahead please.|And?|Hmm... anything else?|Nice, anything more?|Nice! I want to know more :)|And then?|Come on, nothing else?|Un huh, and?"]


function parse_query_string() {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    var query_string = {};
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        var key = decodeURIComponent(pair[0]);
        var value = decodeURIComponent(pair[1]);
        if (typeof query_string[key] === "undefined") {
            query_string[key] = decodeURIComponent(value);
        } else if (typeof query_string[key] === "string") {
            var arr = [query_string[key], decodeURIComponent(value)];
            query_string[key] = arr;
        } else {
            query_string[key].push(decodeURIComponent(value));
        }
    }
    return query_string;
}
