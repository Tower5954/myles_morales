// components/Sidebar.js
import React, { useRef } from 'react';
import { ListGroup, Button } from 'react-bootstrap';
import { FilePlus } from 'react-bootstrap-icons';
import './Sidebar.css';

const Sidebar = ({ files, onFileUpload }) => {
  const fileInputRef = useRef(null);

  const handleFileInputChange = (e) => {
    if (e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(file => ({
        id: Date.now() + Math.random(),
        name: file.name,
        type: file.type,
        size: file.size,
        file: file
      }));
      onFileUpload(newFiles);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h3>Contact Finder</h3>
        <p>Files & Searches</p>
      </div>
      
      <div className="sidebar-controls">
        <Button 
          variant="primary" 
          className="upload-btn"
          onClick={() => fileInputRef.current.click()}
        >
          <FilePlus /> Upload File
        </Button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          multiple
        />
      </div>
      
      <div className="files-section">
        <h5>Files</h5>
        {files.length === 0 ? (
          <p className="no-files">No files uploaded</p>
        ) : (
          <ListGroup>
            {files.map(file => (
              <ListGroup.Item key={file.id} className="file-item">
                {file.name}
                <small>{(file.size / 1024).toFixed(1)} KB</small>
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </div>
      
      <div className="saved-searches">
        <h5>Saved Searches</h5>
        <ListGroup>
          <ListGroup.Item className="search-item">
            bulk_search_contact_details_20250401_145245.csv
          </ListGroup.Item>
          <ListGroup.Item className="search-item">
            bulk_search_email_address_20250401_153130.csv
          </ListGroup.Item>
          <ListGroup.Item className="search-item">
            bulk_search_phone_numbers_20250401_153755.csv
          </ListGroup.Item>
        </ListGroup>
      </div>
    </div>
  );
};

export default Sidebar;