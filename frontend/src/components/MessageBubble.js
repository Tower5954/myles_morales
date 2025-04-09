import React from 'react';
import BotAvatar from './BotAvatar';
import { Person, Download, CheckCircleFill, Circle } from 'react-bootstrap-icons';
import './MessageBubble.css';

const MessageBubble = ({ 
  type, 
  content, 
  urls = [], 
  filename, 
  companies = [],
  evaluation,
  confidenceRating,
  isLoading,
  searchProgress = {}
}) => {
  // Enhanced debugging - log the exact keys in searchProgress
  if (companies && companies.length > 0) {
    console.log("MessageBubble rendering for companies:", companies);
    console.log("isLoading:", isLoading);
    console.log("searchProgress:", searchProgress);
    console.log("searchProgress keys:", Object.keys(searchProgress));
    
    // Try to find matches
    companies.forEach(company => {
      console.log(`Looking for matches for: ${company}`);
      Object.keys(searchProgress).forEach(key => {
        const match = key.includes(company) || company.includes(key);
        console.log(`  Key: ${key}, Match: ${match}`);
      });
    });
  }
  
  return (
    <div className={`message-bubble ${type}-message`}>
      <div className="avatar-container">
        {type === 'bot' ? (
          <BotAvatar size="sm" />
        ) : (
          <div className="user-avatar">
            <Person size={24} />
          </div>
        )}
      </div>
      <div className="message-content">
        <div className="message-sender">
          {type === 'bot' ? 'Myles' : 'You'}
        </div>
        <div className="message-text">{content}</div>
        
        {/* Display confidence rating if available */}
        {confidenceRating && (
          <div className="confidence-rating">
            <span className="rating-label">Confidence Rating:</span> 
            <span className="rating-value">{confidenceRating}</span>
          </div>
        )}
        
        {urls && urls.length > 0 && (
          <div className="message-urls">
            <div className="urls-label">Sources:</div>
            <ul className="urls-list">
              {urls.map((url, index) => (
                <li key={index}>
                  <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Show companies list with progress indicators - Using more flexible matching */}
        {companies && companies.length > 0 && (
          <div className="companies-list">
            <div className="companies-label">Companies:</div>
            <ul className="companies-items">
            {companies.map((company, index) => {
              // Add more detailed debugging
              const found = company in searchProgress;
              const value = found ? searchProgress[company] : 'not found';
              console.log(`Company: ${company}, Found in searchProgress: ${found}, Value: ${value}`);
              
              // Check if this company has been processed
              const isProcessed = searchProgress && company in searchProgress && 
                (searchProgress[company] === true || 
                searchProgress[company] === "True" || 
                searchProgress[company] === 1 ||
                String(searchProgress[company]).toLowerCase() === "true");
              
              return (
                <li key={index} className="company-item">
                  <span className="company-status">
                    {isProcessed ? (
                      <CheckCircleFill className="completed-icon" size={14} />
                    ) : (
                      <Circle className="pending-icon" size={14} />
                    )}
                  </span>
                  {company}
                </li>
              );
            })}
            </ul>
          </div>
        )}
        
        {/* Show download button for bulk search results */}
        {filename && (
          <div className="message-download">
            <a 
              href={`http://localhost:5000/api/direct-download/${encodeURIComponent(filename)}`}
              className="download-link"
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              <Download size={16} /> Download Results CSV
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;