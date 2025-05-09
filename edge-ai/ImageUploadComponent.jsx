import React, { useState } from 'react';
import axios from 'axios';

const ImageUploadComponent = () => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [progress, setProgress] = useState(0);
    
    // Handle file selection
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        
        // Reset states
        setError('');
        setSuccess('');
        setProgress(0);
        
        if (!file) {
            setSelectedFile(null);
            setPreview(null);
            return;
        }
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
            setError('Please select an image file');
            setSelectedFile(null);
            setPreview(null);
            return;
        }
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            setError('File size should be less than 10MB');
            setSelectedFile(null);
            setPreview(null);
            return;
        }
        
        // Set selected file and create preview
        setSelectedFile(file);
        
        // Create preview URL
        const reader = new FileReader();
        reader.onloadend = () => {
            setPreview(reader.result);
        };
        reader.readAsDataURL(file);
    };
    
    // Handle file upload
    const handleUpload = async (event) => {
        event.preventDefault();
        
        if (!selectedFile) {
            setError('Please select a file to upload');
            return;
        }
        
        // Reset states
        setUploading(true);
        setError('');
        setSuccess('');
        setProgress(0);
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Upload file with progress tracking
            const response = await axios.post('/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / progressEvent.total
                    );
                    setProgress(percentCompleted);
                }
            });
            
            // Handle success
            setSuccess('File uploaded successfully!');
            
            // Reset file selection after upload
            setSelectedFile(null);
            setPreview(null);
        } catch (error) {
            console.error('Upload error:', error);
            
            // Handle specific error from edge AI moderation
            if (error.response && error.response.status === 451) {
                setError(`Content violation detected: ${error.response.data.details}`);
            } else {
                setError(
                    error.response?.data?.message || 
                    'An error occurred while uploading the file'
                );
            }
        } finally {
            setUploading(false);
        }
    };
    
    return (
        <div className="image-upload-container">
            <h2>Secure Image Upload</h2>
            <p className="upload-info">
                Images are processed by our AI at the edge for content moderation before being stored.
            </p>
            
            {/* Error message */}
            {error && (
                <div className="error-message">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
                    </svg>
                    {error}
                </div>
            )}
            
            {/* Success message */}
            {success && (
                <div className="success-message">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                    </svg>
                    {success}
                </div>
            )}
            
            {/* Preview */}
            {preview && (
                <div className="preview-container">
                    <img src={preview} alt="Preview" className="image-preview" />
                </div>
            )}
            
            {/* Upload form */}
            <form onSubmit={handleUpload} className="upload-form">
                <div className="file-input-container">
                    <input
                        type="file"
                        id="image-upload"
                        onChange={handleFileChange}
                        accept="image/*"
                        disabled={uploading}
                    />
                    <label htmlFor="image-upload" className={`file-input-label ${uploading ? 'disabled' : ''}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M4.502 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>
                            <path d="M14.002 13a2 2 0 0 1-2 2h-10a2 2 0 0 1-2-2V5A2 2 0 0 1 2 3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-1.998 2zM14 2H4a1 1 0 0 0-1 1h9.002a2 2 0 0 1 2 2v7A1 1 0 0 0 15 11V3a1 1 0 0 0-1-1zM2.002 4a1 1 0 0 0-1 1v8l2.646-2.354a.5.5 0 0 1 .63-.062l2.66 1.773 3.71-3.71a.5.5 0 0 1 .577-.094l1.777 1.947V5a1 1 0 0 0-1-1h-10z"/>
                        </svg>
                        {selectedFile ? selectedFile.name : 'Choose File'}
                    </label>
                </div>
                
                {/* Progress indicator */}
                {uploading && (
                    <div className="progress-container">
                        <div 
                            className="progress-bar" 
                            style={{ width: `${progress}%` }}
                        >
                            {progress}%
                        </div>
                    </div>
                )}
                
                <button
                    type="submit"
                    className="upload-button"
                    disabled={!selectedFile || uploading}
                >
                    {uploading ? 'Uploading...' : 'Upload Image'}
                </button>
            </form>
            
            <div className="security-info">
                <h3>Edge AI Protection</h3>
                <p>
                    Our system uses advanced AI at the network edge to scan images before they reach our servers.
                    This helps protect against inappropriate content and ensures compliance with our terms of service.
                </p>
                <div className="security-features">
                    <div className="feature">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
                        </svg>
                        <span>Content moderation</span>
                    </div>
                    <div className="feature">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
                        </svg>
                        <span>Privacy preserved</span>
                    </div>
                    <div className="feature">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="m8 2.748-.717-.737C5.6.281 2.514.878 1.4 3.053.918 3.995.78 5.323 1.508 7H.43c-2.128-5.697 4.165-8.83 7.394-5.857.06.055.119.112.176.171a3.12 3.12 0 0 1 .176-.17c3.23-2.974 9.522.159 7.394 5.856h-1.078c.728-1.677.59-3.005.108-3.947C13.486.878 10.4.28 8.717 2.01L8 2.748ZM2.212 10h1.315C4.593 11.183 6.05 12.458 8 13.795c1.949-1.337 3.407-2.612 4.473-3.795h1.315c-1.265 1.566-3.14 3.25-5.788 5-2.648-1.75-4.523-3.434-5.788-5Z"/>
                        </svg>
                        <span>Safe environment</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ImageUploadComponent; 