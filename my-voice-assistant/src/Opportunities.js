import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Opportunities.css';

// Sample data for opportunities
const SAMPLE_OPPORTUNITIES = [
  {
    id: 1,
    title: "Software Engineering Intern",
    company: "Google",
    location: "Mountain View, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate"],
    field: ["computer science", "software engineering"],
    description: "Join our team to develop next-generation technologies that change how billions of users connect, explore, and interact with information and one another."
  },
  {
    id: 2,
    title: "Data Science Internship",
    company: "Microsoft",
    location: "Redmond, WA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["data science", "computer science", "statistics"],
    description: "Work with big data and AI to solve complex problems and improve Microsoft's products and services."
  },
  {
    id: 3,
    title: "High School Research Program",
    company: "NASA",
    location: "Houston, TX",
    type: "internship",
    educationLevel: ["high school"],
    field: ["science", "engineering", "research"],
    description: "Experience real-world research and engineering projects at NASA's Johnson Space Center."
  },
  {
    id: 4,
    title: "Marketing Assistant",
    company: "Nike",
    location: "Portland, OR",
    type: "internship",
    educationLevel: ["college", "undergraduate"],
    field: ["marketing", "business", "communications"],
    description: "Assist in developing and implementing marketing strategies for Nike's latest products."
  },
  {
    id: 5,
    title: "Junior Web Developer",
    company: "Spotify",
    location: "New York, NY",
    type: "job",
    educationLevel: ["college", "undergraduate", "bootcamp"],
    field: ["web development", "software engineering"],
    description: "Join our web development team to create and maintain features for Spotify's web application."
  },
  {
    id: 6,
    title: "High School IT Support Intern",
    company: "Local Tech Solutions",
    location: "Chicago, IL",
    type: "internship",
    educationLevel: ["high school"],
    field: ["IT", "computer science"],
    description: "Gain hands-on experience in IT support and troubleshooting while still in high school."
  },
  {
    id: 7,
    title: "Finance Intern",
    company: "JP Morgan Chase",
    location: "New York, NY",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["finance", "accounting", "business"],
    description: "Work alongside financial professionals and gain experience in financial analysis and research."
  },
  {
    id: 8,
    title: "Research Assistant",
    company: "Stanford University",
    location: "Palo Alto, CA",
    type: "job",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["research", "science", "biology"],
    description: "Assist professors with cutting-edge research projects in various scientific fields."
  }
];

// Education level options
const EDUCATION_LEVELS = [
  { value: "high school", label: "High School Student" },
  { value: "high school graduate", label: "High School Graduate" },
  { value: "college", label: "College Student" },
  { value: "undergraduate", label: "Undergraduate" },
  { value: "graduate", label: "Graduate Student" },
  { value: "bootcamp", label: "Bootcamp" }
];

// Interest/Field options
const FIELDS = [
  "Computer Science",
  "Software Engineering",
  "Web Development",
  "Data Science",
  "AI/Machine Learning",
  "Business",
  "Marketing",
  "Finance",
  "Accounting",
  "Engineering",
  "Science",
  "Research",
  "IT",
  "Communications",
  "Statistics",
  "Biology"
];

function Opportunities() {
  const [location, setLocation] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [field, setField] = useState('');
  const [showResults, setShowResults] = useState(false);
  
  // Filter opportunities based on search criteria
  const filteredOpportunities = SAMPLE_OPPORTUNITIES.filter(opportunity => {
    const locationMatch = !location || 
      opportunity.location.toLowerCase().includes(location.toLowerCase());
    
    const educationMatch = !educationLevel || 
      opportunity.educationLevel.includes(educationLevel.toLowerCase());
    
    const fieldMatch = !field || 
      opportunity.field.some(f => f.toLowerCase().includes(field.toLowerCase()));
    
    return locationMatch && educationMatch && fieldMatch;
  });
  
  const handleSearch = (e) => {
    e.preventDefault();
    setShowResults(true);
  };
  
  return (
    <div className="opportunities-page">
      <div className="background-square"></div>
      
      {/* Navigation Bar - same as main app for consistency */}
      <nav className="navbar">
        <div className="navbar-brand">Interview AI</div>
        <div className="navbar-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/opportunities" className="nav-link active">Internship/Job Opportunities</Link>
        </div>
      </nav>
      
      <div className="opportunities-container">
        <h1>Find Internships & Job Opportunities</h1>
        <p className="subtitle">Discover opportunities that match your location, education level, and interests</p>
        
        <div className="search-section">
          <form onSubmit={handleSearch}>
            <div className="search-filters">
              <div className="filter-group">
                <label htmlFor="location">Location</label>
                <input 
                  type="text" 
                  id="location" 
                  placeholder="City, State, or Remote"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
              </div>
              
              <div className="filter-group">
                <label htmlFor="education">Education Level</label>
                <select 
                  id="education"
                  value={educationLevel}
                  onChange={(e) => setEducationLevel(e.target.value)}
                >
                  <option value="">All Education Levels</option>
                  {EDUCATION_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label htmlFor="field">Field/Interest</label>
                <select 
                  id="field"
                  value={field}
                  onChange={(e) => setField(e.target.value)}
                >
                  <option value="">All Fields</option>
                  {FIELDS.map(field => (
                    <option key={field} value={field}>{field}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <button type="submit" className="search-button">
              Search Opportunities
            </button>
          </form>
        </div>
        
        {showResults && (
          <div className="results-section">
            <h2>Search Results ({filteredOpportunities.length})</h2>
            
            {filteredOpportunities.length === 0 ? (
              <div className="no-results">
                <p>No opportunities found matching your criteria. Try adjusting your search filters.</p>
              </div>
            ) : (
              <div className="opportunities-list">
                {filteredOpportunities.map(opportunity => (
                  <div key={opportunity.id} className="opportunity-card">
                    <h3>{opportunity.title}</h3>
                    <div className="opportunity-details">
                      <p className="company"><strong>{opportunity.company}</strong></p>
                      <p className="location">{opportunity.location}</p>
                      <p className="type">{opportunity.type === 'internship' ? 'Internship' : 'Job'}</p>
                    </div>
                    <p className="description">{opportunity.description}</p>
                    <div className="opportunity-tags">
                      {opportunity.educationLevel.map(level => (
                        <span key={level} className="tag education-tag">
                          {level.charAt(0).toUpperCase() + level.slice(1)}
                        </span>
                      ))}
                      {opportunity.field.slice(0, 2).map(field => (
                        <span key={field} className="tag field-tag">
                          {field.charAt(0).toUpperCase() + field.slice(1)}
                        </span>
                      ))}
                    </div>
                    <button className="apply-button">Apply Now</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="opportunities-info">
          <h2>How to Make the Most of Your Search</h2>
          <div className="info-cards">
            <div className="info-card">
              <h3>For High School Students</h3>
              <p>Look for research programs, shadowing opportunities, and summer internships that welcome high school students. These experiences can help you explore potential career paths and build your college applications.</p>
            </div>
            <div className="info-card">
              <h3>For College Students</h3>
              <p>Internships, co-ops, and research positions can provide valuable experience in your field of study. Many companies offer opportunities specifically for undergraduate and graduate students.</p>
            </div>
            <div className="info-card">
              <h3>Prepare for Interviews</h3>
              <p>Once you find opportunities that interest you, use our <Link to="/">Interview AI</Link> to practice your interview skills and receive valuable feedback.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Opportunities; 