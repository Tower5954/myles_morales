import React, { useState, useRef, useEffect } from 'react';
import { Form, InputGroup, Button } from 'react-bootstrap';
import { Send } from 'react-bootstrap-icons';
import MessageBubble from './MessageBubble';
import BotAvatar from './BotAvatar';
import GLoader from './GLoader';
import './ChatContainer.css';

const ChatContainer = ({ messages, onSendMessage, searchProgress }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Add a debug log to check searchProgress
  useEffect(() => {
    console.log("ChatContainer received searchProgress:", searchProgress);
  }, [searchProgress]);
  
  useEffect(() => {
    // Check if any message has isLoading=true
    const loadingMessage = messages.find(msg => msg.isLoading);
    setIsLoading(!!loadingMessage);
    
    // Scroll to bottom
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };
  
  return (
    <div className="chat-container">
      <div className="chat-header">
        <BotAvatar />
        <div className="bot-info">
          <h4>Myles</h4>
          <p>Contact Finder Assistant</p>
        </div>
      </div>
      
      <div className="messages-container">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loader-container">
              <GLoader size={120} color="#26A6AB" speed={80} />
              <div className="loading-text">Searching for contact information...</div>
            </div>
          </div>
        )}
        
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Contact Finder</h3>
            <p>
              I can help you find business contact information from websites.
              Try asking me to find contacts for a business, or upload a list 
              of companies to search in bulk.
            </p>
            <div className="sample-queries">
              <h5>Try these examples:</h5>
              <ul>
                <li>"Find contact info for Lee's Custom Woodwork"</li>
                <li>"Search for email addresses from Geab"</li>
                <li>"Extract phone numbers from Pulse Controls"</li>
              </ul>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            // Debug log to check what message is being rendered
            if (msg.companies && msg.companies.length > 0) {
              console.log(`Rendering message ${index} with companies:`, msg.companies);
              console.log(`Message ${index} isLoading:`, msg.isLoading);
              console.log(`Message ${index} has searchProgress:`, msg.searchProgress);
              console.log(`Global searchProgress:`, searchProgress);
            }
            
            return (
              <MessageBubble 
                key={index} 
                type={msg.type} 
                content={msg.content}
                urls={msg.urls} 
                filename={msg.filename}
                companies={msg.companies}
                evaluation={msg.evaluation} 
                confidenceRating={msg.confidenceRating}
                isLoading={msg.isLoading}
                // Use the message's own searchProgress if available, otherwise use the global one
                searchProgress={msg.searchProgress || searchProgress}
              />
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <Form onSubmit={handleSubmit} className="message-input-form">
        <InputGroup>
          <Form.Control
            placeholder="Type your query here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <Button variant="primary" type="submit" disabled={isLoading}>
            <Send />
          </Button>
        </InputGroup>
      </Form>
    </div>
  );
};

export default ChatContainer;