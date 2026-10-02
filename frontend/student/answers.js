document.addEventListener(
    "DOMContentLoaded",
    async function () {

        console.log("ANSWERS PAGE LOADED");


        // =========================================================
        // API BASE URL
        // =========================================================

        const API_BASE_URL =
            window.API_BASE_URL;


        // =========================================================
        // GET TOKEN
        // =========================================================

        const token =
            localStorage.getItem(
                "access_token"
            );


        if (!token) {

            console.error(
                "No access token found."
            );

            return;

        }


        // =========================================================
        // GET ATTEMPT ID
        // =========================================================

        const requestedAttemptId =
            new URLSearchParams(window.location.search).get("attempt");
        let attemptId =
            requestedAttemptId ||
            localStorage.getItem(
                "last_attempt_id"
            );

        if (requestedAttemptId) {
            localStorage.setItem("last_attempt_id", requestedAttemptId);
        }


        /*
         * If the attempt ID was saved inside
         * last_exam_result, use that as fallback.
         */

        if (!attemptId) {

            try {

                const savedResult =
                    JSON.parse(
                        localStorage.getItem(
                            "last_exam_result"
                        ) || "null"
                    );


                if (
                    savedResult &&
                    savedResult.attempt_id
                ) {

                    attemptId =
                        savedResult.attempt_id;

                }

            } catch (error) {

                console.error(
                    "Could not read saved result:",
                    error
                );

            }

        }


        if (!attemptId) {

            console.error(
                "No attempt ID found."
            );

            alert(
                "Exam result information could not be found."
            );

            return;

        }


        console.log(
            "Loading result for attempt:",
            attemptId
        );


        // =========================================================
        // HELPER
        // =========================================================

        function setText(
            id,
            value
        ) {

            const element =
                document.getElementById(id);


            if (element) {

                element.textContent =
                    value;

            }

        }


        // =========================================================
        // FORMAT NUMBER
        // =========================================================

        function formatNumber(
            value
        ) {

            const number =
                Number(value);


            if (
                Number.isInteger(number)
            ) {

                return String(number);

            }


            return number.toFixed(2);

        }


        // =========================================================
        // LOAD RESULT FROM BACKEND
        // =========================================================

        async function loadResult() {

            const url =
                `${API_BASE_URL}/api/attempts/` +
                `${encodeURIComponent(attemptId)}/result`;


            console.log(
                "RESULT API:",
                url
            );


            try {

                const response =
                    await fetch(
                        url,
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


                console.log(
                    "RESULT STATUS:",
                    response.status
                );


                if (!response.ok) {

                    const errorText =
                        await response.text();


                    console.error(
                        "RESULT API ERROR:",
                        errorText
                    );


                    throw new Error(
                        `Result API returned ${response.status}`
                    );

                }


                const data =
                    await response.json();


                console.log(
                    "RESULT DATA:",
                    data
                );


                /*
                 * Save result so the review page
                 * can also use it.
                 */

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


                renderResult(
                    data
                );


            } catch (error) {

                console.error(
                    "Failed to load result:",
                    error
                );


                showError();

            }

        }


        // =========================================================
        // RENDER RESULT
        // =========================================================

        function renderResult(
            data
        ) {

            const total =
                Number(
                    data.total_questions || 0
                );


            const correct =
                Number(
                    data.correct_answers || 0
                );


            const wrong =
                Number(
                    data.wrong_answers || 0
                );


            const unanswered =
                Number(
                    data.unanswered || 0
                );


            const score =
                Number(
                    data.score || 0
                );


            const percentage =
                Number(
                    data.percentage || 0
                );


            const questions =
                Array.isArray(
                    data.questions
                )
                    ? data.questions
                    : [];


            // =====================================================
            // MAIN RESULT
            // =====================================================

            setText(
                "resultPercentage",
                `${formatNumber(percentage)}%`
            );


            setText(
                "resultScore",
                formatNumber(score)
            );


            setText(
                "correctAnswers",
                correct
            );


            setText(
                "wrongAnswers",
                wrong
            );


            setText(
                "unansweredAnswers",
                unanswered
            );


            // =====================================================
            // TEST NAME
            // =====================================================

            if (
                data.exam_title
            ) {

                setText(
                    "resultTestName",
                    data.exam_title
                );

            }

            else if (
                data.exam_id
            ) {

                setText(
                    "resultTestName",
                    `Exam ${data.exam_id}`
                );

            }

            else {

                setText(
                    "resultTestName",
                    "EPS TOPIK Exam"
                );

            }


            // =====================================================
            // EXAM TYPE
            // =====================================================

            setText(
                "resultExamType",
                "EPS TOPIK Examination"
            );


            // =====================================================
            // RESULT STATUS
            // =====================================================

            setText(
                "resultStatus",
                "COMPLETED"
            );


            // =====================================================
            // RESULT MESSAGE
            // =====================================================

            setText(
                "resultMessage",
                `You answered ${correct} of ${total} questions correctly.`
            );


            // =====================================================
            // HEADER
            // =====================================================

            setText(
                "resultHeaderLabel",
                "EXAM COMPLETED"
            );


            setText(
                "resultHeaderTitle",
                "Exam Result"
            );


            setText(
                "resultHeaderMessage",
                "Your examination result is shown below."
            );


            // =====================================================
            // ACTION MESSAGE
            // =====================================================

            setText(
                "resultActionMessage",
                "Review your answers to see which questions you got right, wrong, or left unanswered."
            );


            // =====================================================
            // SECTION PERFORMANCE
            // =====================================================

            renderSectionPerformance(
                questions
            );


            // =====================================================
            // QUESTION OVERVIEW
            // =====================================================

            renderQuestionOverview(
                questions
            );

        }


        // =========================================================
        // QUESTION STATUS
        // =========================================================

        function getQuestionStatus(
            question
        ) {

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


        // =========================================================
        // SECTION PERFORMANCE
        // =========================================================

        function renderSectionPerformance(
            questions
        ) {

            const reading =
                questions.filter(
                    question => {

                        const type =
                            String(
                                question.question_type ||
                                ""
                            ).toLowerCase();


                        return (
                            type === "reading" ||
                            type === "read"
                        );

                    }
                );


            const listening =
                questions.filter(
                    question => {

                        const type =
                            String(
                                question.question_type ||
                                ""
                            ).toLowerCase();


                        return (
                            type === "listening" ||
                            type === "listen"
                        );

                    }
                );


            renderSection(
                "reading",
                reading
            );


            renderSection(
                "listening",
                listening
            );

        }


        // =========================================================
        // RENDER ONE SECTION
        // =========================================================

        function renderSection(
            section,
            questions
        ) {

            const percentageElement =
                document.getElementById(
                    section === "reading"
                        ? "readingPercentage"
                        : "listeningPercentage"
                );


            const barElement =
                document.getElementById(
                    section === "reading"
                        ? "readingBar"
                        : "listeningBar"
                );


            const correctElement =
                document.getElementById(
                    section === "reading"
                        ? "readingCorrect"
                        : "listeningCorrect"
                );


            const scoreElement =
                document.getElementById(
                    section === "reading"
                        ? "readingScore"
                        : "listeningScore"
                );


            const total =
                questions.length;


            const correct =
                questions.filter(
                    question =>
                        getQuestionStatus(
                            question
                        ) === "correct"
                ).length;


            const wrong =
                questions.filter(
                    question =>
                        getQuestionStatus(
                            question
                        ) === "wrong"
                ).length;


            const unanswered =
                questions.filter(
                    question =>
                        getQuestionStatus(
                            question
                        ) === "unanswered"
                ).length;


            /*
             * We only show a percentage when
             * the backend actually gave us
             * questions for this section.
             */

            if (total === 0) {

                if (percentageElement) {

                    percentageElement.textContent =
                        "—";

                }


                if (barElement) {

                    barElement.style.width =
                        "0%";

                }


                if (correctElement) {

                    correctElement.textContent =
                        "No questions";

                }


                if (scoreElement) {

                    scoreElement.textContent =
                        "";

                }


                return;

            }


            const percentage =
                (
                    correct /
                    total
                ) * 100;


            if (percentageElement) {

                percentageElement.textContent =
                    `${formatNumber(percentage)}%`;

            }


            if (barElement) {

                barElement.style.width =
                    `${percentage}%`;

            }


            if (correctElement) {

                correctElement.textContent =
                    `${correct} / ${total} Correct`;

            }


            if (scoreElement) {

                scoreElement.textContent =
                    `${wrong} Incorrect • ${unanswered} Unanswered`;

            }

        }


        // =========================================================
        // QUESTION OVERVIEW
        // =========================================================

        function renderQuestionOverview(
            questions
        ) {

            const grid =
                document.getElementById(
                    "questionResultGrid"
                );


            if (!grid) {

                return;

            }


            grid.innerHTML =
                "";


            questions.forEach(
                (
                    question,
                    index
                ) => {

                    const button =
                        document.createElement(
                            "button"
                        );


                    button.type =
                        "button";


                    button.className =
                        "question-result-button";


                    const status =
                        getQuestionStatus(
                            question
                        );


                    if (
                        status === "correct"
                    ) {

                        button.classList.add(
                            "correct"
                        );

                    }

                    else if (
                        status === "wrong"
                    ) {

                        button.classList.add(
                            "wrong"
                        );

                    }

                    else {

                        button.classList.add(
                            "unanswered"
                        );

                    }


                    button.textContent =
                        question.question_number ??
                        index + 1;


                    /*
                     * Clicking a question opens
                     * the review page.
                     */

                    button.addEventListener(
                        "click",
                        function () {

                            window.location.href =
                                "review-answer.html";

                        }
                    );


                    grid.appendChild(
                        button
                    );

                }
            );

        }


        // =========================================================
        // ERROR STATE
        // =========================================================

        function showError() {

            setText(
                "resultPercentage",
                "—"
            );


            setText(
                "resultScore",
                "—"
            );


            setText(
                "correctAnswers",
                "—"
            );


            setText(
                "wrongAnswers",
                "—"
            );


            setText(
                "unansweredAnswers",
                "—"
            );


            setText(
                "resultStatus",
                "RESULT UNAVAILABLE"
            );


            setText(
                "resultMessage",
                "Your exam was submitted successfully, but the result is temporarily unavailable. Refresh this page shortly; you do not need to submit again."
            );

        }


        // =========================================================
        // REVIEW ANSWERS
        // =========================================================

        window.reviewAnswers =
            function () {

                window.location.href =
                    "review-answer.html";

            };


        // =========================================================
        // RETAKE TEST
        // =========================================================

        window.retakeTest =
            function () {

                const examId =
                    localStorage.getItem(
                        "last_exam_id"
                    );


                const setId =
                    localStorage.getItem(
                        "last_set_id"
                    );


                if (
                    examId &&
                    setId
                ) {

                    window.location.href =
                        `exam.html?exam=${encodeURIComponent(examId)}` +
                        `&set=${encodeURIComponent(setId)}`;

                    return;

                }


                window.location.href =
                    "set.html";

            };


        // =========================================================
        // DASHBOARD
        // =========================================================

        window.goToDashboard =
            function () {

                window.location.href =
                    "dashboard.html";

            };


        // =========================================================
        // LOGOUT
        // =========================================================

        window.logout =
            function () {

                localStorage.removeItem(
                    "access_token"
                );

                localStorage.removeItem(
                    "token_type"
                );

                window.location.href =
                    "login.html";

            };


        // =========================================================
        // DOWNLOAD RESULT
        // =========================================================

        window.downloadResult =
            function () {

                const testName =
                    document.getElementById(
                        "resultTestName"
                    )?.textContent ||
                    "EPS TOPIK Exam";


                const percentage =
                    document.getElementById(
                        "resultPercentage"
                    )?.textContent ||
                    "—";


                const score =
                    document.getElementById(
                        "resultScore"
                    )?.textContent ||
                    "—";


                const correct =
                    document.getElementById(
                        "correctAnswers"
                    )?.textContent ||
                    "—";


                const wrong =
                    document.getElementById(
                        "wrongAnswers"
                    )?.textContent ||
                    "—";


                const unanswered =
                    document.getElementById(
                        "unansweredAnswers"
                    )?.textContent ||
                    "—";


                const resultText =

`EPS TOPIK EXAM RESULT

Test: ${testName}

Score: ${score}

Percentage: ${percentage}

Correct Answers: ${correct}

Incorrect Answers: ${wrong}

Unanswered: ${unanswered}

EPS TOPIK Exam Platform
`;


                const file =
                    new Blob(
                        [resultText],
                        {
                            type:
                                "text/plain"
                        }
                    );


                const url =
                    URL.createObjectURL(
                        file
                    );


                const link =
                    document.createElement(
                        "a"
                    );


                link.href =
                    url;


                link.download =
                    "EPS-TOPIK-Result.txt";


                document.body.appendChild(
                    link
                );


                link.click();


                document.body.removeChild(
                    link
                );


                URL.revokeObjectURL(
                    url
                );

            };


        // =========================================================
        // START
        // =========================================================

        await loadResult();

    }
);
