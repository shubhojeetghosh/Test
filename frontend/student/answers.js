document.addEventListener(
    "DOMContentLoaded",
    async function () {




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

            const scoreCircle =
                document.querySelector(
                    ".result-score-circle"
                );

            if (scoreCircle) {
                const boundedPercentage = Math.min(
                    100,
                    Math.max(0, Number.isFinite(percentage) ? percentage : 0)
                );

                scoreCircle.style.setProperty(
                    "--score-progress",
                    `${boundedPercentage}%`
                );
            }


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

            document.querySelector(
                ".result-score-circle"
            )?.style.setProperty("--score-progress", "0%");

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

                fetch(`${window.API_BASE_URL || ""}/auth/logout`, {
                    method: "POST",
                    keepalive: true
                }).catch(() => {});

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


                const safeText = (value) => String(value ?? "—")
                    .normalize("NFKD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .replace(/[^\x20-\x7E]/g, "?");
                const pdfEscape = (value) => safeText(value)
                    .replace(/\\/g, "\\\\")
                    .replace(/\(/g, "\\(")
                    .replace(/\)/g, "\\)");
                const text = (x, y, value, size = 12, font = "F1", color = "0.12 0.18 0.29") =>
                    `BT /${font} ${size} Tf ${color} rg 1 0 0 1 ${x} ${y} Tm (${pdfEscape(value)}) Tj ET\n`;
                const rect = (x, y, width, height, fill, stroke = null) => {
                    let command = `${fill} rg ${x} ${y} ${width} ${height} re `;
                    command += stroke ? `${stroke} RG B\n` : "f\n";
                    return command;
                };

                const generatedAt = new Date().toLocaleDateString("en-US", {
                    year: "numeric", month: "long", day: "numeric"
                });
                let content = "";
                content += rect(0, 720, 595, 122, "0.08 0.14 0.27");
                content += rect(0, 716, 595, 4, "0.16 0.39 0.91");
                content += text(48, 790, "EPS TOPIK EXAM PLATFORM", 11, "F2", "0.71 0.80 1.00");
                content += text(48, 754, "Exam Result", 26, "F2", "1 1 1");
                content += text(48, 735, `Generated ${generatedAt}`, 10, "F1", "0.84 0.88 0.96");

                content += text(48, 675, "TEST", 9, "F2", "0.30 0.39 0.55");
                content += text(48, 650, testName, 17, "F2");
                content += text(48, 620, "Your performance summary", 11, "F1", "0.36 0.42 0.52");

                const metrics = [
                    { label: "FINAL SCORE", value: score, x: 48, y: 500 },
                    { label: "PERCENTAGE", value: percentage, x: 310, y: 500 },
                    { label: "CORRECT ANSWERS", value: correct, x: 48, y: 390 },
                    { label: "INCORRECT ANSWERS", value: wrong, x: 310, y: 390 },
                    { label: "UNANSWERED", value: unanswered, x: 48, y: 280, width: 499 }
                ];
                metrics.forEach(({ label, value, x, y, width = 237 }) => {
                    content += rect(x, y, width, 82, "0.96 0.97 0.99", "0.86 0.89 0.93");
                    content += text(x + 16, y + 54, label, 9, "F2", "0.36 0.43 0.56");
                    content += text(x + 16, y + 25, value, 19, "F2", "0.08 0.15 0.29");
                });
                content += text(48, 115, "Keep practicing and build on your progress.", 12, "F1", "0.23 0.31 0.46");
                content += "0.86 0.89 0.93 RG 48 82 m 547 82 l S\n";
                content += text(48, 58, "EPS TOPIK Exam Platform  |  Practice, Learn, Improve", 9, "F1", "0.42 0.48 0.58");

                const stream = `${content}\n`;
                const objects = [
                    "<< /Type /Catalog /Pages 2 0 R >>",
                    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
                    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
                    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
                    `<< /Length ${stream.length} >>\nstream\n${stream}endstream`
                ];
                let pdf = "%PDF-1.4\n% EPS TOPIK Result\n";
                const offsets = [0];
                objects.forEach((object, index) => {
                    offsets.push(pdf.length);
                    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
                });
                const xrefOffset = pdf.length;
                pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
                for (let index = 1; index < offsets.length; index += 1) {
                    pdf += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
                }
                pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

                const file = new Blob([pdf], { type: "application/pdf" });
                const url = URL.createObjectURL(file);
                const link = document.createElement("a");
                const filename = safeText(testName)
                    .replace(/[^A-Za-z0-9]+/g, "-")
                    .replace(/^-|-$/g, "") || "EPS-TOPIK";
                link.href = url;
                link.download = `${filename}-Result.pdf`;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.setTimeout(() => URL.revokeObjectURL(url), 1000);

            };


        // =========================================================
        // START
        // =========================================================

        await loadResult();

    }
);
