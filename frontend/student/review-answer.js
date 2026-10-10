document.addEventListener("DOMContentLoaded", async function () {

    // ============================================================
    // ELEMENTS
    // ============================================================

    const totalElement =
        document.getElementById("reviewTotal");

    const correctElement =
        document.getElementById("reviewCorrect");

    const wrongElement =
        document.getElementById("reviewWrong");

    const unansweredElement =
        document.getElementById("reviewUnanswered");

    const questionList =
        document.getElementById("reviewQuestionList");

    const loadingElement =
        document.getElementById("reviewLoading");

    const filterButtons =
        document.querySelectorAll(".review-filter");

    const backToResultButton =
        document.getElementById("backToResult");

    const dashboardButton =
        document.getElementById("goToDashboard");


    // ============================================================
    // STATE
    // ============================================================

    let activeFilter = "all";

    let questions = [];


    // ============================================================
    // API BASE URL
    // ============================================================

    const API_BASE_URL = window.API_BASE_URL || "";


    // ============================================================
    // GET LOGIN TOKEN
    // ============================================================

    const token =
        localStorage.getItem("access_token");


    // ============================================================
    // GET LAST ATTEMPT
    // ============================================================

    let resultData = null;

    const storedResult =
        localStorage.getItem("last_exam_result");


    if (storedResult) {

        try {

            resultData =
                JSON.parse(storedResult);

        } catch (error) {

            console.error(
                "Failed to read saved exam result:",
                error
            );

        }

    }


    // ============================================================
    // GET ATTEMPT ID
    // ============================================================

    let attemptId = null;


    if (resultData && resultData.attempt_id) {

        attemptId =
            resultData.attempt_id;

    }


    // Also check possible standalone storage.
    if (!attemptId) {

        attemptId =
            localStorage.getItem(
                "last_attempt_id"
            );

    }


    // ============================================================
    // VALIDATE
    // ============================================================

    if (!token) {

        console.error(
            "No access token found."
        );

        if (loadingElement) {

            loadingElement.textContent =
                "Your login session has expired. Please login again.";

        }

        return;
    }


    if (!attemptId) {

        console.error(
            "No attempt ID found."
        );

        if (loadingElement) {

            loadingElement.textContent =
                "No exam attempt was found. Please complete an exam first.";

        }

        return;
    }


    // ============================================================
    // LOAD RESULT FROM BACKEND
    // ============================================================

    async function loadResult() {

        try {

            if (loadingElement) {

                loadingElement.style.display =
                    "block";

                loadingElement.textContent =
                    "Loading your answers...";

            }


            const resultUrl =
                `${API_BASE_URL}/api/attempts/` +
                `${encodeURIComponent(attemptId)}/result`;





            const response =
                await fetch(
                    resultUrl,
                    {
                        method: "GET",

                        headers: {
                            "Authorization":
                                `Bearer ${token}`,

                            "Content-Type":
                                "application/json"
                        }
                    }
                );





            if (!response.ok) {

                const errorText =
                    await response.text();

                console.error(
                    "Result API error:",
                    errorText
                );

                throw new Error(
                    `Failed to load result (${response.status})`
                );
            }


            const data =
                await response.json();




            resultData = data;


            // Save latest result again.
            localStorage.setItem(
                "last_exam_result",
                JSON.stringify(data)
            );


            if (data.attempt_id) {

                localStorage.setItem(
                    "last_attempt_id",
                    data.attempt_id
                );

            }


            // ----------------------------------------------------
            // QUESTIONS
            // ----------------------------------------------------

            questions =
                Array.isArray(data.questions)
                    ? data.questions
                    : [];


            updateSummary(data);

            renderQuestions();


            if (loadingElement) {

                loadingElement.style.display =
                    "none";

            }


        } catch (error) {

            console.error(
                "Failed to load review:",
                error
            );


            if (loadingElement) {

                loadingElement.style.display =
                    "block";

                loadingElement.textContent =
                    "Unable to load your answers. Please try again.";

            }

        }

    }


    // ============================================================
    // UPDATE SUMMARY
    // ============================================================

    function updateSummary(data) {

        if (totalElement) {

            totalElement.textContent =
                data.total_questions ?? questions.length;

        }


        if (correctElement) {

            correctElement.textContent =
                data.correct_answers ?? 0;

        }


        if (wrongElement) {

            wrongElement.textContent =
                data.wrong_answers ?? 0;

        }


        if (unansweredElement) {

            unansweredElement.textContent =
                data.unanswered ?? 0;

        }

    }


    // ============================================================
    // QUESTION STATUS
    // ============================================================

    function getQuestionStatus(question) {

        const selected =
            question.selected_option_id;

        const correct =
            question.correct_option_id;


        if (!selected) {

            return "unanswered";

        }


        if (
            String(selected) ===
            String(correct)
        ) {

            return "correct";

        }


        return "wrong";

    }


    // ============================================================
    // GET OPTION LABEL
    // ============================================================

    function getOptionLabel(
        question,
        optionId
    ) {

        if (!optionId) {

            return null;

        }


        const index =
            question.options.findIndex(
                option =>
                    String(option.id) ===
                    String(optionId)
            );


        if (index === -1) {

            return null;

        }


        return String.fromCharCode(
            65 + index
        );

    }


    // ============================================================
    // GET OPTION TEXT
    // ============================================================

    function getOptionText(
        question,
        optionId
    ) {

        if (!optionId) {

            return "Not Answered";

        }


        const option =
            question.options.find(
                item =>
                    String(item.id) ===
                    String(optionId)
            );


        if (!option) {

            return "Unknown Answer";

        }


        const label =
            getOptionLabel(
                question,
                optionId
            );


        return label
            ? `${label}. ${option.text}`
            : option.text;

    }


    // ============================================================
    // CREATE OPTION
    // ============================================================

    function createOptionElement(
        question,
        option,
        index
    ) {

        const optionElement =
            document.createElement("div");


        optionElement.className =
            "review-answer";


        const optionId =
            String(option.id);


        const selectedId =
            question.selected_option_id
                ? String(
                    question.selected_option_id
                )
                : null;


        const correctId =
            question.correct_option_id
                ? String(
                    question.correct_option_id
                )
                : null;


        const isCorrect =
            optionId === correctId;


        const isSelected =
            optionId === selectedId;


        // Correct option
        if (isCorrect) {

            optionElement.classList.add(
                "correct-answer"
            );

        }


        // Selected but incorrect
        if (
            isSelected &&
            !isCorrect
        ) {

            optionElement.classList.add(
                "wrong-answer"
            );

        }


        const label =
            document.createElement("span");


        label.textContent =
            String.fromCharCode(
                65 + index
            );


        const text =
            document.createElement("span");


        text.textContent =
            option.text || "";


        optionElement.appendChild(
            label
        );


        optionElement.appendChild(
            text
        );

        if (option.image_url) {
            const image = document.createElement("img");
            image.className = "review-option-image";
            image.alt = `Option ${String.fromCharCode(65 + index)} image`;
            image.src = resolveReviewMediaUrl(option.image_url);
            image.onerror = () => image.remove();
            optionElement.appendChild(image);
        }

        if (option.audio_url) {
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.preload = "none";
            audio.src = resolveReviewMediaUrl(option.audio_url);
            audio.addEventListener("click", (event) => event.stopPropagation());
            optionElement.appendChild(audio);
        }


        return optionElement;

    }

    function resolveReviewMediaUrl(value) {
        const source = String(value || "").trim();
        if (!source) return "";
        if (/^(?:data:|blob:|https?:\/\/)/i.test(source)) return source;
        const base = window.API_BASE_URL || window.location.origin;
        try {
            return new URL(source, `${base.replace(/\/+$/, "")}/`).href;
        } catch (error) {
            console.warn("Could not resolve review media URL:", error);
            return source;
        }
    }


    // ============================================================
    // CREATE QUESTION CARD
    // ============================================================

    function createQuestionCard(
        question,
        index
    ) {

        const status =
            getQuestionStatus(question);


        const card =
            document.createElement("article");


        card.className =
            "review-question-card";


        // --------------------------------------------------------
        // HEADER
        // --------------------------------------------------------

        const header =
            document.createElement("div");


        header.className =
            "review-question-header";


        const number =
            document.createElement("span");


        number.className =
            "review-question-number";


        number.textContent =
            `QUESTION ${
                question.question_number ??
                index + 1
            }`;


        const statusElement =
            document.createElement("span");


        statusElement.className =
            "review-status";


        if (status === "correct") {

            statusElement.classList.add(
                "correct-status"
            );

            statusElement.textContent =
                "Correct";

        } else if (status === "wrong") {

            statusElement.classList.add(
                "wrong-status"
            );

            statusElement.textContent =
                "Incorrect";

        } else {

            statusElement.classList.add(
                "unanswered-status"
            );

            statusElement.textContent =
                "Unanswered";

        }


        header.appendChild(
            number
        );


        header.appendChild(
            statusElement
        );


        // --------------------------------------------------------
        // QUESTION TEXT
        // --------------------------------------------------------

        const questionText =
            document.createElement("p");


        questionText.className =
            "review-question-text";


        questionText.textContent =
            question.text || "";


        // --------------------------------------------------------
        // IMAGE
        // --------------------------------------------------------

        if (question.image_url) {

            const image =
                document.createElement("img");


            image.src =
                resolveReviewMediaUrl(question.image_url);
            image.onerror = () => image.remove();


            image.alt =
                "Question image";


            image.style.maxWidth =
                "100%";


            image.style.marginBottom =
                "20px";


            card.appendChild(
                image
            );

        }

        if (question.audio_url) {
            const audio = document.createElement("audio");
            audio.controls = true;
            audio.preload = "none";
            audio.src = resolveReviewMediaUrl(question.audio_url);
            card.appendChild(audio);
        }


        // --------------------------------------------------------
        // OPTIONS
        // --------------------------------------------------------

        const optionList =
            document.createElement("div");


        optionList.className =
            "review-answer-list";


        if (
            Array.isArray(
                question.options
            )
        ) {

            question.options.forEach(
                (
                    option,
                    optionIndex
                ) => {

                    optionList.appendChild(
                        createOptionElement(
                            question,
                            option,
                            optionIndex
                        )
                    );

                }
            );

        }


        // --------------------------------------------------------
        // ANSWER INFO
        // --------------------------------------------------------

        const answerInfo =
            document.createElement("div");


        answerInfo.className =
            "review-answer-info";


        const yourAnswerBox =
            document.createElement("div");


        const yourAnswerLabel =
            document.createElement("span");


        yourAnswerLabel.textContent =
            "Your Answer";


        const yourAnswer =
            document.createElement("strong");


        yourAnswer.textContent =
            getOptionText(
                question,
                question.selected_option_id
            );


        yourAnswerBox.appendChild(
            yourAnswerLabel
        );


        yourAnswerBox.appendChild(
            yourAnswer
        );


        const correctAnswerBox =
            document.createElement("div");


        const correctAnswerLabel =
            document.createElement("span");


        correctAnswerLabel.textContent =
            "Correct Answer";


        const correctAnswer =
            document.createElement("strong");


        correctAnswer.classList.add(
            "correct-text"
        );


        correctAnswer.textContent =
            getOptionText(
                question,
                question.correct_option_id
            );


        correctAnswerBox.appendChild(
            correctAnswerLabel
        );


        correctAnswerBox.appendChild(
            correctAnswer
        );


        if (status === "wrong") {

            yourAnswer.classList.add(
                "wrong-text"
            );

        }


        if (status === "unanswered") {

            yourAnswer.classList.add(
                "wrong-text"
            );

        }


        answerInfo.appendChild(
            yourAnswerBox
        );


        answerInfo.appendChild(
            correctAnswerBox
        );


        // --------------------------------------------------------
        // ADD EVERYTHING
        // --------------------------------------------------------

        card.appendChild(
            header
        );


        card.appendChild(
            questionText
        );


        card.appendChild(
            optionList
        );


        card.appendChild(
            answerInfo
        );


        return card;

    }


    // ============================================================
    // RENDER QUESTIONS
    // ============================================================

    function renderQuestions() {

        if (!questionList) {

            return;

        }


        questionList.innerHTML =
            "";


        const filteredQuestions =
            questions.filter(
                question => {

                    const status =
                        getQuestionStatus(
                            question
                        );


                    return (
                        activeFilter === "all" ||
                        status === activeFilter
                    );

                }
            );


        if (
            filteredQuestions.length === 0
        ) {

            const empty =
                document.createElement("p");


            empty.textContent =
                "No questions found for this filter.";


            questionList.appendChild(
                empty
            );


            return;

        }


        filteredQuestions.forEach(
            (
                question,
                index
            ) => {

                questionList.appendChild(
                    createQuestionCard(
                        question,
                        index
                    )
                );

            }
        );

    }


    // ============================================================
    // FILTER BUTTONS
    // ============================================================

    filterButtons.forEach(
        button => {

            button.addEventListener(
                "click",
                function () {

                    filterButtons.forEach(
                        item => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    this.classList.add(
                        "active"
                    );


                    activeFilter =
                        this.dataset.filter ||
                        "all";


                    renderQuestions();

                }
            );

        }
    );


    // ============================================================
    // BACK TO RESULT
    // ============================================================

    if (backToResultButton) {

        backToResultButton.addEventListener(
            "click",
            function () {

                window.location.href =
                    "answers.html";

            }
        );

    }


    // ============================================================
    // GO TO DASHBOARD
    // ============================================================

    if (dashboardButton) {
    dashboardButton.addEventListener(
        "click",
        function () {
            window.location.href =
                "dashboard.html";
        }
    );
}

    // ============================================================
    // LOAD
    // ============================================================

    await loadResult();

});
