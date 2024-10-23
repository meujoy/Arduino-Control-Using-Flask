let commands = ["close relay00","open relay00","close relay01","open relay01"]
let commandsObject = {};
let subCommands = {};
let commandCounter = 1;
const subConsoleElement = document.querySelector('#consoleSubCommands');
const jsonConsoleElement = document.querySelector('#consoleJSON');
const keyTextElement = document.querySelector('.js-command-gui');
const errorMessageElement = document.querySelector('#error-message');



window.onload = function() {
    showCommands(); 
    validateRealtime();
};

function showCommands () {

    const dropdownElement = document.querySelector('.js-dropdown-menu');

    let commandsHTML = '';
    for (let i =0; i<commands.length;i++){
        const command = commands[i];

        const html = `<option value="${command}">${command}</option>`

        commandsHTML += html;
    }
    dropdownElement.innerHTML = commandsHTML;
}

function addCommand (){
    if (commandCounter >= 1){
        const command = document.querySelector('.js-dropdown-menu').value;
        subCommands[`command${commandCounter}`] = command;
        commandCounter += 1;
        displayCommands(subConsoleElement,subCommands);
        validateInput();
    }else{
        commandCounter = 1;
        validateInput();
    }
}

function deleteCommand() {
    if (commandCounter-1 >= 1) {
        delete subCommands[`command${commandCounter-1}`];
        commandCounter -=1;
        displayCommands(subConsoleElement,subCommands);   
    }else{
        commandCounter = 1;
    }  
}

function nextBlock() {
    if (validateInput()){
        const commandKey= keyTextElement.value;
        commandsObject[commandKey] = subCommands;
        displayCommands(jsonConsoleElement,commandsObject);
        cleanUp();
    }
    
}

function displayCommands(element,object) {
    if (Object.keys(object).length >= 1) {
        element.value = JSON.stringify(object,null,2);
    }else{
        element.value = '';
    }
}

function cleanUp() {
    subCommands = {};
    commandCounter = 1;
    subConsoleElement.value = '';
    keyTextElement.value = '';

}

function validateRealtime() {
    // Validates input using validateInput() by listening to events while user is inputing data in the textbox
    keyTextElement.addEventListener('input',function(){
        validateInput();
    });

    // Validates input using validateInput() by listening to events when user selects outside the textbox
    keyTextElement.addEventListener('blur',function(){
        validateInput();
    });
}

function validateInput() {
    let isValid = true;
    let value = keyTextElement.value;

    let empty = value === '' ? true : false;
    let space = hasSpacesInMiddle(value);
    let duplicate = keyExists(value);
    let subCommandsEmpty = Object.keys(subCommands).length === 0;

    if (space || duplicate || empty || subCommandsEmpty) {
        isValid = false;
        if (space) {
            errorMessageElement.innerHTML = "Spaces aren't allowed";
            errorMessageElement.style.display ='Block';
        }else if (duplicate){
            errorMessageElement.innerHTML = "Key cannot be duplicated";
            errorMessageElement.style.display ='Block';
        }else if (empty){
            errorMessageElement.innerHTML = 'Key cannot be empty';
            errorMessageElement.style.display ='Block';
        }else if (subCommandsEmpty) {
            errorMessageElement.innerHTML = "Command blocks cannot be empty";
            errorMessageElement.style.display ='Block';
        }
        
    } else {
        errorMessageElement.style.display = 'none';
    }

    blockUnblockBtns(isValid);

    return isValid;
}

function blockUnblockBtns(isValid) {
    const doneBtnElement = document.querySelector('#doneBtn');
    const nextBlockBtnElement = document.querySelector('#nextBlockBtn');
    const resetBtnElement = document.querySelector('#resetBtn');
    doneBtnElement.disabled = !isValid;
    nextBlockBtnElement.disabled = !isValid;
    resetBtnElement.disabled = !isValid;
}

function keyExists(value) {
    if (Object.keys(commandsObject).includes(value)) {
        return true;
    }
    return false;
}

function hasSpacesInMiddle(value) {
    return value.trim().length > 0 && /\s/.test(value.trim());
}

function submitJson() {
    fetch('/submit',
        {
            method: 'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body:JSON.stringify(commandsObject),
        })
        .then(response => response.json())
        .then(data =>{
            console.log('Success',data);
            if (data.redirect_url) {
                window.location.href = data.redirect_url; // Redirect to the new page
            }
        })
        .catch((error) =>{
            console.error('Error',error);
        });
}



