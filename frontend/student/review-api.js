
async function getReviewData() {
    /*
     * Temporary frontend testing mode.
     */


    /*
     * This section will be used when the backend is ready.
     *
     * The backend developer will later provide:
     * - The actual endpoint
     * - The attempt ID
     * - The authentication requirements
     */
    const attemptId = sessionStorage.getItem("attemptId");

    if (!attemptId) {
        throw new Error("No exam attempt ID was found.");
    }

    const endpoint = REVIEW_CONFIG.REVIEW_ENDPOINT.replace(
        "{attemptId}",
        encodeURIComponent(attemptId)
    );

    const response = await fetch(
        `${REVIEW_CONFIG.API_BASE_URL}${endpoint}`,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        }
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load review data. Status: ${response.status}`
        );
    }

    const backendData = await response.json();

    return normalizeReviewData(backendData);
}


/*
 * Converts different possible backend field names
 * into the structure expected by review-answers.js.
 */
function normalizeReviewData(data) {
    const backendQuestions = data.questions || data.items || [];

    const normalizedQuestions = backendQuestions.map(
        (question, index) => {
            const rawOptions =
                question.options ||
                question.choices ||
                [];

            const normalizedOptions = rawOptions.map(
                (option, optionIndex) => {
                    /*
                     * Supports option objects such as:
                     * { label: "A", text: "물" }
                     *
                     * and simple strings such as:
                     * "물"
                     */
                    if (typeof option === "string") {
                        return {
                            label: String.fromCharCode(65 + optionIndex),
                            text: option
                        };
                    }

                    return {
                        label:
                            option.label ||
                            option.key ||
                            String.fromCharCode(65 + optionIndex),

                        text:
                            option.text ||
                            option.value ||
                            option.option_text ||
                            ""
                    };
                }
            );

            return {
                id:
                    question.id ||
                    question.question_id ||
                    index + 1,

                question:
                    question.question ||
                    question.question_text ||
                    question.text ||
                    "",

                options: normalizedOptions,

                selectedAnswer:
                    question.selectedAnswer ??
                    question.selected_answer ??
                    question.answer ??
                    null,

                correctAnswer:
                    question.correctAnswer ??
                    question.correct_answer ??
                    question.correct_option ??
                    null
            };
        }
    );

    return {
        total_questions:
            data.total_questions ||
            normalizedQuestions.length,

        questions: normalizedQuestions
    };
}