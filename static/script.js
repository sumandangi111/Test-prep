// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    const quizForm = document.getElementById('quiz-form');
    const nextButton = document.getElementById('next-btn');

    if (quizForm && nextButton) {
        quizForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Find the selected radio button
            const selectedOption = quizForm.querySelector('input[name="answer"]:checked');
            
            if (!selectedOption) {
                alert("Please select an answer before proceeding.");
                return;
            }

            // Temporarily disable the button to prevent double-submission
            nextButton.disabled = true;
            nextButton.textContent = 'Processing...';

            const formData = new FormData();
            formData.append('answer', selectedOption.value);

            try {
                // Send the answer to the Flask backend using the Fetch API
                const response = await fetch('/submit_answer', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                // Redirect the user based on the backend response
                if (data.redirect) {
                    window.location.href = data.redirect;
                }

            } catch (error) {
                console.error('Error submitting answer:', error);
                alert('An error occurred. Please try again.');
            } finally {
                // Re-enable the button if an error occurred before redirect
                nextButton.disabled = false;
                nextButton.textContent = 'Next';
            }
        });
    }
});