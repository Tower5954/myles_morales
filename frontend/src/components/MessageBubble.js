import React from 'react';
import BotAvatar from './BotAvatar';
import { Person, Download } from 'react-bootstrap-icons';
import './MessageBubble.css';

const MessageBubble = ({ 
  type, 
  content, 
  urls = [], 
  filename, 
  companies = [],
  evaluation,
  confidenceRating
}) => {
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
        
        {/* Show companies list if provided */}
        {companies && companies.length > 0 && (
          <div className="companies-list">
            <div className="companies-label">Companies:</div>
            <ul className="companies-items">
              {companies.slice(0, 5).map((company, index) => (
                <li key={index}>{company}</li>
              ))}
              {companies.length > 5 && <li>...and {companies.length - 5} more</li>}
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