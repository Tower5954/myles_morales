import React from 'react';
import './BotAvatar.css';

const BotAvatar = ({ size = "md" }) => {
  return (
    <div className={`bot-avatar avatar-${size}`}>
      <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="45" fill="#26A6AB" />
        <circle cx="35" cy="40" r="5" fill="white" />
        <circle cx="65" cy="40" r="5" fill="white" />
        <path
          d="M35 65 Q50 80 65 65"
          stroke="white"
          strokeWidth="4"
          fill="transparent"
        />
      </svg>
    </div>
  );
};

export default BotAvatar;