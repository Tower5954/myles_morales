// src/services/api.js
const API_URL = 'http://localhost:5000/api';

export const findContact = async (query, url = null, interactive = false) => {
  try {
    const response = await fetch(`${API_URL}/find`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query, 
        url, 
        interactive,
        evaluate: true  
      }),
    });
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Global variable to store the progress callback reference
let currentProgressCallback = null;

// Function that can be called to update progress
window.updateCompanyProgress = function(companyName) {
  if (currentProgressCallback && typeof currentProgressCallback === 'function') {
    currentProgressCallback(companyName);
    console.log(`Progress updated for: ${companyName}`);
    return true;
  }
  return false;
};

export const bulkSearch = async (names, query, progressCallback = null) => {
  try {
    // Store the callback function in the global variable
    currentProgressCallback = progressCallback;
    
    // Make the actual API call
    const response = await fetch(`${API_URL}/bulk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ names, query }),
    });
    
    return await response.json();
  } catch (error) {
    currentProgressCallback = null;
    return { success: false, error: error.message };
  }
};

export const getSavedSearches = async () => {
  try {
    const response = await fetch(`${API_URL}/saved-searches`);
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
};

export const uploadFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    return await response.json();
  } catch (error) {
    return { success: false, error: error.message };
  }
};