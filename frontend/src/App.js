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
      const thinkingMessages = [...newMessages, { 
        type: 'bot', 
        content: `Searching for "${message}" across ${lastBotMessage.companies.length} companies...`,
        isLoading: true
      }];
      
      setMessages(thinkingMessages);
      
      try {
        // Call bulk search API with the companies and the query
        const result = await bulkSearch(lastBotMessage.companies, message);
        
        // Remove the thinking message
        const updatedMessages = thinkingMessages.filter(msg => !msg.isLoading);
        
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
        
        setMessages(updatedMessages);
      } catch (error) {
        // Handle any unexpected errors
        const updatedMessages = thinkingMessages.filter(msg => !msg.isLoading);
        updatedMessages.push({
          type: 'bot',
          content: `An error occurred during bulk search: ${error.message || 'Unknown error'}`
        });
        setMessages(updatedMessages);
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
          />
        </Col>
      </Row>
    </Container>
  );
}

export default App;