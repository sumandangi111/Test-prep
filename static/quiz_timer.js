// static/quiz_timer.js

document.addEventListener('DOMContentLoaded', () => {
    const timerElement = document.getElementById('timer');
    const quizForm = document.getElementById('quiz-form');
    const nextButton = document.getElementById('next-btn');
    let timeLeft = 15; // Set the time limit (15 seconds)
    let countdown;

    if (timerElement && quizForm) {
        
        // Start the countdown timer
        countdown = setInterval(() => {
            timeLeft -= 1;
            timerElement.textContent = timeLeft;

            if (timeLeft <= 5) {
                timerElement.style.color = '#dc3545'; // Red color for low time
            }

            if (timeLeft <= 0) {
                clearInterval(countdown); // Stop timer
                alert("Time's up! Submitting answer.");
                // Submit null answer if time runs out
                submitAnswer(null); 
            }
        }, 1000);

        // Form submission handler
        quizForm.addEventListener('submit', (e) => {
            e.preventDefault();
            clearInterval(countdown); // Stop timer immediately
            
            const selectedOption = quizForm.querySelector('input[name="answer"]:checked');
            submitAnswer(selectedOption ? selectedOption.value : null);
        });
    }

    async function submitAnswer(answerValue) {
        // Disable UI to prevent interaction during feedback
        document.querySelectorAll('.options input').forEach(input => input.disabled = true);
        nextButton.disabled = true;
        nextButton.textContent = "Processing...";

        const formData = new FormData();
        // Send selected answer or empty string if time ran out
        formData.append('answer', answerValue || ''); 

        try {
            // 1. Submit answer for scoring and get feedback data
            const response = await fetch('/submit_answer', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            // 2. Show Visual Feedback (Green/Red)
            showFeedback(data.correct_answer_text, data.user_answer_text);

            nextButton.textContent = "Continuing...";
            
            // 3. Wait 3 seconds to let the user see the feedback
            setTimeout(async () => {
                
                // 4. Send second request to advance the server index
                const advanceResponse = await fetch('/advance_question', { method: 'POST' });
                const advanceData = await advanceResponse.json();
                
                // 5. Redirect based on the advancement response
                if (advanceData.redirect) {
                    window.location.href = advanceData.redirect;
                }
            }, 3000); // 3-second delay

        } catch (error) {
            console.error('Error submitting answer:', error);
            alert('An error occurred. Please try again.');
            nextButton.disabled = false;
            nextButton.textContent = "Submit & Next";
        }
    }

    function showFeedback(correctText, userText) {
        document.querySelectorAll('.options label').forEach(label => {
            const input = label.querySelector('input');
            const isUserSelection = input.value === userText;
            const isCorrectAnswer = input.value === correctText;
            
            // Add base class for styling
            label.classList.add('feedback'); 
            
            if (isCorrectAnswer) {
                // Always mark the correct answer green
                label.classList.add('correct');
            } else if (isUserSelection && !isCorrectAnswer) {
                // Mark user's selection red if it was wrong
                label.classList.add('incorrect');
            }
        });
    }
});