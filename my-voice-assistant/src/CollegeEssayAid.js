import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './App.css';
import './CollegeEssayAid.css';

function CollegeEssayAid() {
  const [essayText, setEssayText] = useState('');
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Function to get API base URL
  const getApiBaseUrl = () => {
    const hostname = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol;
    
    // Local development
    if (hostname === 'localhost' && port === '3000') {
      return 'http://localhost:5001';
    } 
    // Production environments
    else {
      return `${protocol}//${hostname}${port ? ':' + port : ''}`;
    }
  };

  const API_BASE_URL = getApiBaseUrl();

  // Handle essay submission
  const handleSubmitEssay = async (e) => {
    e.preventDefault();
    
    if (!essayText.trim()) {
      setError('Please enter your essay text');
      return;
    }

    setIsSubmitting(true);
    setError('');
    setFeedback('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          text: `You are an expert college essay reviewer. Please analyze this college essay and provide EXTREMELY COMPREHENSIVE AND DETAILED feedback with AT LEAST 8-10 TOTAL PARAGRAPHS of analysis spread across multiple sections. Your response MUST include:
          
1. OVERALL ASSESSMENT (at least 2 full paragraphs): Thoroughly evaluate the essay's strengths, potential, and general impression. First paragraph should discuss strengths, and second paragraph should cover overall weaknesses.

2. STRUCTURE AND ORGANIZATION (at least 2 full paragraphs): Provide detailed analysis of how well the essay is structured, with specific examples from the beginning, middle, and end of the essay. Discuss both what works and what needs improvement.

3. CONTENT DEVELOPMENT (at least 2 full paragraphs): Critically analyze the depth, authenticity, and effectiveness of the content. Provide specific examples from the text showing where content is strong and where it needs more development.

4. LANGUAGE AND STYLE (at least 2 full paragraphs): Thoroughly evaluate the language, style, grammar, and mechanics. Quote at least 3-4 specific sentences from the essay and provide suggestions for improvement.

5. RECOMMENDATIONS (at least 2 full paragraphs): Provide specific, actionable recommendations for improvement. First paragraph should focus on big-picture improvements, and second paragraph should address specific details.

FOR EACH SECTION, YOU MUST WRITE MULTIPLE WELL-DEVELOPED PARAGRAPHS (not just bullet points or short sentences). A proper paragraph contains at least 4-5 sentences. Your analysis should be specific to this essay, not generic advice. DO NOT be brief - be thorough and detailed.

Here's the essay: ${essayText}`,
          purpose: 'essay_feedback'
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setFeedback(data.response || 'No feedback received');
    } catch (error) {
      setError('Failed to get feedback. Please try again later.');
      console.error('Error submitting essay:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="App">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">🧠 Forge Future</div>
        <div className="navbar-links">
          <Link to="/essay-aid" className="nav-link active">College Essay Aid</Link>
          <Link to="/opportunities" className="nav-link">Internship/Job Opportunities</Link>
          <Link to="/" className="nav-link">Interview AI</Link>
        </div>
      </nav>

      <div className="container">
        <h1 style={{ color: '#7e57c2' }}>🧠 College Essay Aid</h1>
        <p className="subtitle">Get specific, detailed feedback on your college application essays</p>
        
        <div className="essay-container two-column">
          <div className="essay-input-column">
            <form onSubmit={handleSubmitEssay}>
              <div className="form-group">
                <label htmlFor="essayText">Paste your essay below:</label>
                <textarea
                  id="essayText"
                  className="essay-input"
                  value={essayText}
                  onChange={(e) => setEssayText(e.target.value)}
                  placeholder="Enter your college essay here (250-650 words recommended)"
                  rows={18}
                />
                <div className="word-count">
                  Word count: {essayText.trim() ? essayText.trim().split(/\s+/).length : 0}
                </div>
              </div>
              
              <div className="essay-instructions">
                <h3>How This Works:</h3>
                <ul>
                  <li>Our AI will provide specific, actionable suggestions</li>
                  <li>You'll receive detailed feedback on sentence structure, clarity, and content</li>
                  <li>We highlight exactly what to improve and how to improve it</li>
                  <li>We <strong>will not</strong> rewrite your essay for you</li>
                </ul>
              </div>

              <button 
                type="submit" 
                className="submit-button"
                disabled={isSubmitting || !essayText.trim()}
              >
                {isSubmitting ? 'Getting Feedback...' : 'Get Essay Feedback'}
              </button>
            </form>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>

          <div className="feedback-column">
            {feedback ? (
              <div className="feedback-container">
                <h2>Feedback on Your Essay</h2>
                <div className="feedback-content">
                  {feedback.split('\n').map((paragraph, index) => {
                    // Check if paragraph is a bullet point or heading
                    if (paragraph.trim().startsWith('•') || paragraph.trim().startsWith('-')) {
                      return <li key={index}>{paragraph.replace(/^[•-]\s*/, '')}</li>;
                    } else if (paragraph.trim().endsWith(':')) {
                      // Treat as a heading
                      return <h3 key={index}>{paragraph}</h3>;
                    } else if (paragraph.trim()) {
                      return <p key={index}>{paragraph}</p>;
                    }
                    return null;
                  })}
                </div>
              </div>
            ) : (
              <div className="empty-feedback">
                <h2>Your Feedback Will Appear Here</h2>
                <p>Submit your essay to receive detailed, actionable feedback to help improve your writing.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CollegeEssayAid; 