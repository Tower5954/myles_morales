// App.js
import React, { useState, useEffect } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/ChatContainer';
import { findContact, getSavedSearches, uploadFile, bulkSearch } from './services/api';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [searchProgress, setSearchProgress] = useState({});

  // Debug log for searchProgress changes
  useEffect(() => {
    console.log("App searchProgress updated:", searchProgress);
  }, [searchProgress]);

  useEffect(() => {
    // Load saved searches when component mounts
    const loadSavedSearches = async () => {
      const result = await getSavedSearches();
      if (result.success) {
        setFiles(result.searches.map(filename => ({
          id: Date.now() + Math.random(),
          name: filename,
          type: 'search',
        })));
      }
    };
    
    loadSavedSearches();
  }, []);

  const handleFileUpload = async (newFiles) => {
    // Handle the actual file upload
    const file = newFiles[0].file;
    const result = await uploadFile(file);
    
    if (result.success) {
      setFiles([...files, ...newFiles]);
      // If it's a companies list, prompt for search query
      if (result.companies && result.companies.length > 0) {
        // Initialize search progress for each company
        const initialProgress = {};
        result.companies.forEach(company => {
          initialProgress[company] = false; // Not searched yet
        });
        console.log("Initializing search progress:", initialProgress);
        setSearchProgress(initialProgress);
        
        setMessages([...messages, {
          type: 'bot',
          content: `Found ${result.companies.length} companies in the file. What would you like to search for across these companies? (e.g., "email addresses", "phone numbers", "contact information")`,
          companies: result.companies,
          expectingQuery: true  // Flag to indicate we're expecting a query
        }]);
      } else {
        setMessages([...messages, {
          type: 'bot',
          content: `File uploaded successfully: ${result.message || file.name}`
        }]);
      }
    } else {
      // Show error message
      setMessages([...messages, {
        type: 'bot',
        content: `Error uploading file: ${result.error}`
      }]);
    }
  };

  
  const handleSendMessage = async (message) => {
    // Add user message to chat
    const newMessages = [...messages, { type: 'user', content: message }];
    setMessages(newMessages);
    
    // Check if this is a response to a company list query prompt
    const lastBotMessage = messages.filter(msg => msg.type === 'bot').pop();
    if (lastBotMessage && lastBotMessage.expectingQuery && lastBotMessage.companies) {
      // User is providing a search query for the companies
      console.log("Starting bulk search for companies:", lastBotMessage.companies);
      console.log("Current search progress:", searchProgress);
      
      // Create a loading message with companies
      const thinkingMessages = [...newMessages, { 
        type: 'bot', 
        content: `Searching for "${message}" across ${lastBotMessage.companies.length} companies...`,
        isLoading: true, // This should be true for the progress indicators to show
        companies: lastBotMessage.companies,
        // Use the current search progress
        searchProgress: {...searchProgress} 
      }];
      
      setMessages(thinkingMessages);
      
      try {
        // Call modified bulk search API that reports progress
        const result = await bulkSearch(
          lastBotMessage.companies, 
          message,
          // Progress callback function
          (company) => {
            console.log(`Progress callback triggered for: ${company}`);
            
            // Update the search progress for this company
            setSearchProgress(prev => {
              const newProgress = {
                ...prev,
                [company]: true // Mark this company as searched
              };
              console.log(`Updated searchProgress:`, newProgress);
              return newProgress;
            });
            
            // Update the loading message to show updated progress
            setMessages(prevMessages => {
              // Find the loading message
              const updatedMessages = [...prevMessages];
              const loadingMsgIndex = updatedMessages.findIndex(msg => msg.isLoading);
              
              if (loadingMsgIndex !== -1) {
                // Create a new message object with updated searchProgress
                const updatedLoadingMsg = {
                  ...updatedMessages[loadingMsgIndex],
                  searchProgress: {
                    ...updatedMessages[loadingMsgIndex].searchProgress,
                    [company]: true
                  }
                };
                
                console.log(`Updating loading message with progress for ${company}:`, 
                  updatedLoadingMsg.searchProgress);
                
                // Replace the old message with the updated one
                updatedMessages[loadingMsgIndex] = updatedLoadingMsg;
              }
              
              return updatedMessages;
            });
          }
        );
        
        // Remove the thinking message after search completes
        const updatedMessages = newMessages.filter(msg => !msg.isLoading);
        
        if (result.success) {
          // Extract just the filename from the filepath
          const filepath = result.filepath;
          const filename = filepath ? filepath.split('/').pop() : null;
          
          // Add the result message with the filename
          updatedMessages.push({
            type: 'bot',
            content: `Bulk search completed! ${result.message}`,
            filename: filename  // Store just the filename for direct download
          });
        } else {
          // Add error message
          updatedMessages.push({
            type: 'bot',
            content: `Error processing bulk search: ${result.error}`
          });
        }
        
        // Update messages and reset progress
        setMessages(updatedMessages);
        console.log("Bulk search complete, resetting progress");
        setSearchProgress({});
      } catch (error) {
        console.error("Error in bulk search:", error);
        // Handle any unexpected errors
        const updatedMessages = newMessages.filter(msg => !msg.isLoading);
        updatedMessages.push({
          type: 'bot',
          content: `An error occurred during bulk search: ${error.message || 'Unknown error'}`
        });
        setMessages(updatedMessages);
        // Reset search progress after error
        setSearchProgress({});
      }
    } else {
      // Regular contact search
      // Add a "thinking" message with loading state
      const thinkingMessages = [...newMessages, { 
        type: 'bot', 
        content: 'Searching for information...',
        isLoading: true
      }];
      
      setMessages(thinkingMessages);
      
      try {
        // Call API with evaluation
        const result = await findContact(message, null, false, true); 
        
        // Remove the thinking message 
        const updatedMessages = thinkingMessages.filter(msg => !msg.isLoading);
        
        if (result.success) {
          // Add the result message with evaluation data if available
          updatedMessages.push({
            type: 'bot',
            content: result.results.text || 'No information found',
            urls: result.results.urls,
            evaluation: result.results.evaluation, // Include the evaluation data
            confidenceRating: result.results.evaluation?.confidence 
              ? (result.results.evaluation.confidence / 100).toFixed(1) 
              : null
          });
        } else {
          // Add error message
          updatedMessages.push({
            type: 'bot',
            content: `Error processing your request: ${result.error}`
          });
        }
        
        setMessages(updatedMessages);
      } catch (error) {
        // Handle any unexpected errors
        const updatedMessages = thinkingMessages.filter(msg => !msg.isLoading);
        updatedMessages.push({
          type: 'bot',
          content: `An error occurred: ${error.message || 'Unknown error'}`
        });
        setMessages(updatedMessages);
      }
    }
  };

  return (
    <Container fluid className="app-container">
      <Row className="h-100">
        <Col md={3} className="sidebar-col">
          <Sidebar files={files} onFileUpload={handleFileUpload} />
        </Col>
        <Col md={9} className="chat-col">
          <ChatContainer 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            searchProgress={searchProgress}
          />
        </Col>
      </Row>
    </Container>
  );
}

export default App;