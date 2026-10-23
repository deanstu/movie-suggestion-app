const tagContainer = document.getElementById('tagContainer');
const usernameForm = document.getElementById('usernameForm');
const usernameInput = document.getElementById('usernameInput');
const usernamesListDisplay = document.getElementById('usernamesListDisplay');
const usernameSubmit = document.getElementById('submitUsername');


// Master list storage holding all validated usernames
let usernamesList = [];

// Focus the hidden input if user clicks empty container area
tagContainer.addEventListener('click', () => {
  usernamesInput.focus();
});

// Capture keydown events on the text field
usernameInput.addEventListener('keydown', (event) => {
  // Check if Enter key was hit
  if (event.key === 'Enter') {
    event.preventDefault(); // Stop standard form submission
    
    const value = usernameInput.value.trim();
    
    // Add value if it isn't empty and isn't a duplicate
    if (value && !usernamesList.includes(value)) {
      usernamesList.push(value);
      createTagPill(value);
      usernameInput.value = ''; // Reset field for next entry
    }
  }
});

// Capture username when button clicked
usernameSubmit.addEventListener('click', (event) => {
  event.preventDefault(); // Stop standard form submission
    
  const value = usernameInput.value.trim();
    
  // Add value if it isn't empty and isn't a duplicate
  if (value && !usernamesList.includes(value)) {
    usernamesList.push(value);
    createTagPill(value);
    usernameInput.value = ''; // Reset field for next entry
  }
});

// Function to generate the visual Tag Pill element
function createTagPill(username) {
  const pill = document.createElement('div');
  pill.className = 'tag-pill';
  pill.setAttribute('data-username', username);
  
  pill.innerHTML = `
    <span>${username}</span>
    <button type="button" class="remove-btn">&times;</button>
  `;
  
  // Insert the new element inside container right before the input field
  tagContainer.append(pill);
}

// Remove tag workflow utilizing event delegation
tagContainer.addEventListener('click', (event) => {
  if (event.target.classList.contains('remove-btn')) {
    const pillElement = event.target.parentElement;
    const usernameToRemove = pillElement.getAttribute('data-username');
    
    // Filter item out of master data array
    usernamesList = usernamesList.filter(user => user !== usernameToRemove);
    
    // Remove the pill from screen layout
    pillElement.remove();
  }
});

// Capture final batch submission
usernameForm.addEventListener('submit', (event) => {
  if (usernamesList.length === 0) {
    event.preventDefault();
    return;
  }

  usernamesListDisplay.value = JSON.stringify(usernamesList);
});