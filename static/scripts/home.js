function sendCommand(event) {
    event.preventDefault();  // Prevent default form submission

    // Get the selected command from the dropdown
    const command = document.getElementById('Commands').value;
    const consoleElement = document.getElementById('Console');
    
    const sendButton = document.querySelector('button[type="submit"]');

    if (consoleElement) {
        // Append "Sending..." to the textarea
        consoleElement.value += '\nSending...';

        sendButton.disabled = true;
        sendButton.innerHTML = "Sending...";

        // Send the command to the Flask server via AJAX (fetch)
        fetch('/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: command })
            // returns a promise
        })
        .then(response => response.json())
        .then(data => {
            // Append the final message to the textarea
            consoleElement.value += '\n' + data.message;

            sendButton.disabled = false;
            sendButton.innerHTML = "Send Command";
        })
        .catch(error => {
            // Handle errors and append error message
            consoleElement.value += '\nError: ' + error.message;
        });
    } else {
        console.error('Console element not found!');
    }
}

function resetCommands() {
    fetch('/reset-commands', {
        method: 'DELETE',
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            // If response is not ok, still attempt to parse JSON to get the message
            return response.json().then(errorData => {
                throw new Error(errorData.message || 'Something went wrong');
            });
        }
    })
    .then(data => {
        console.log('Success:', data.message);
        // Redirect to the URL specified in the response
        if (data.redirect_url) {
            window.location.href = data.redirect_url; // Redirecting to the new URL
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
