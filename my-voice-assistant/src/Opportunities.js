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
    description: "Join our team to develop next-generation technologies that change how billions of users connect, explore, and interact with information and one another.",
    url: "https://careers.google.com/students/"
  },
  {
    id: 2,
    title: "Data Science Internship",
    company: "Microsoft",
    location: "Redmond, WA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["data science", "computer science", "statistics"],
    description: "Work with big data and AI to solve complex problems and improve Microsoft's products and services.",
    url: "https://careers.microsoft.com/students/"
  },
  {
    id: 3,
    title: "High School Research Program",
    company: "NASA",
    location: "Houston, TX",
    type: "internship",
    educationLevel: ["high school"],
    field: ["science", "engineering", "research"],
    description: "Experience real-world research and engineering projects at NASA's Johnson Space Center.",
    url: "https://www.nasa.gov/stem/highschool/student-pathways/"
  },
  {
    id: 4,
    title: "Marketing Assistant",
    company: "Nike",
    location: "Portland, OR",
    type: "internship",
    educationLevel: ["college", "undergraduate"],
    field: ["marketing", "business", "communications"],
    description: "Assist in developing and implementing marketing strategies for Nike's latest products.",
    url: "https://jobs.nike.com/internships"
  },
  {
    id: 5,
    title: "Junior Web Developer",
    company: "Spotify",
    location: "New York, NY",
    type: "job",
    educationLevel: ["college", "undergraduate", "bootcamp"],
    field: ["web development", "software engineering"],
    description: "Join our web development team to create and maintain features for Spotify's web application.",
    url: "https://www.spotifyjobs.com/students/"
  },
  {
    id: 6,
    title: "High School IT Support Intern",
    company: "Local Tech Solutions",
    location: "Chicago, IL",
    type: "internship",
    educationLevel: ["high school"],
    field: ["IT", "computer science"],
    description: "Gain hands-on experience in IT support and troubleshooting while still in high school.",
    url: "https://www.indeed.com/q-High-School-Internship-jobs.html"
  },
  {
    id: 7,
    title: "Finance Intern",
    company: "JP Morgan Chase",
    location: "New York, NY",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["finance", "accounting", "business"],
    description: "Work alongside financial professionals and gain experience in financial analysis and research.",
    url: "https://careers.jpmorgan.com/us/en/students/programs"
  },
  {
    id: 8,
    title: "Research Assistant",
    company: "Stanford University",
    location: "Palo Alto, CA",
    type: "job",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["research", "science", "biology"],
    description: "Assist professors with cutting-edge research projects in various scientific fields.",
    url: "https://careers.stanford.edu/students/"
  },
  {
    id: 9,
    title: "UI/UX Design Intern",
    company: "Adobe",
    location: "San Jose, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["design", "UI/UX", "graphic design"],
    description: "Apply your design skills to create beautiful and intuitive user interfaces for Adobe products.",
    url: "https://www.adobe.com/careers/university.html"
  },
  {
    id: 10,
    title: "Product Management Intern",
    company: "Amazon",
    location: "Seattle, WA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["product management", "business", "technology"],
    description: "Drive the development and launch of new features and products that millions of customers will use.",
    url: "https://www.amazon.jobs/en/teams/internships-for-students"
  },
  {
    id: 11,
    title: "High School Science Program",
    company: "National Institutes of Health",
    location: "Bethesda, MD",
    type: "internship",
    educationLevel: ["high school"],
    field: ["science", "biology", "research"],
    description: "Participate in hands-on research projects alongside NIH scientists and gain exposure to biomedical research.",
    url: "https://www.training.nih.gov/programs/hs-sip"
  },
  {
    id: 12,
    title: "Environmental Science Intern",
    company: "Environmental Protection Agency",
    location: "Washington, DC",
    type: "internship",
    educationLevel: ["high school", "college", "undergraduate"],
    field: ["environmental science", "biology", "chemistry"],
    description: "Contribute to projects that help protect the environment and human health through scientific research.",
    url: "https://www.epa.gov/careers/student-internships"
  },
  {
    id: 13,
    title: "High School Business Apprenticeship",
    company: "Bank of America",
    location: "Charlotte, NC",
    type: "internship",
    educationLevel: ["high school"],
    field: ["business", "finance", "economics"],
    description: "Learn about banking, finance, and business operations through hands-on experience.",
    url: "https://careers.bankofamerica.com/en-us/students-and-graduates"
  },
  {
    id: 14,
    title: "Journalism Intern",
    company: "Local Newspaper",
    location: "Various Locations",
    type: "internship",
    educationLevel: ["high school", "college"],
    field: ["journalism", "writing", "communications"],
    description: "Develop writing skills by contributing articles and learning about news reporting.",
    url: "https://www.journalismjobs.com/internships"
  },
  {
    id: 15,
    title: "Healthcare Volunteer Program",
    company: "Children's Hospital",
    location: "Boston, MA",
    type: "internship",
    educationLevel: ["high school"],
    field: ["healthcare", "medicine", "volunteer"],
    description: "Volunteer in a hospital setting to gain exposure to healthcare careers and help patients.",
    url: "https://www.childrenshospital.org/workforce-development/internship-opportunities"
  },
  {
    id: 16,
    title: "Robotics Engineering Intern",
    company: "Boston Dynamics",
    location: "Waltham, MA",
    type: "internship",
    educationLevel: ["high school", "college"],
    field: ["robotics", "engineering", "programming"],
    description: "Work with cutting-edge robotics technology and learn about mechanical and software engineering.",
    url: "https://www.bostondynamics.com/careers"
  },
  {
    id: 17,
    title: "Cybersecurity Analyst Intern",
    company: "Cisco Systems",
    location: "San Jose, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["cybersecurity", "computer science", "IT"],
    description: "Help protect networks and data from cyber threats while learning from industry professionals.",
    url: "https://www.cisco.com/c/en/us/about/careers/working-at-cisco/students-and-new-graduate-programs.html"
  },
  {
    id: 18,
    title: "App Developer Internship",
    company: "Apple",
    location: "Cupertino, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["mobile development", "software engineering", "UI design"],
    description: "Develop innovative apps for iOS devices and work with cutting-edge Apple technologies.",
    url: "https://www.apple.com/careers/us/students.html"
  },
  {
    id: 19,
    title: "Mechanical Engineering Intern",
    company: "Tesla",
    location: "Fremont, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["mechanical engineering", "automotive", "design"],
    description: "Work on revolutionary electric vehicles and contribute to sustainable transportation solutions.",
    url: "https://www.tesla.com/careers/students"
  },
  {
    id: 20,
    title: "Climate Research Program",
    company: "NOAA",
    location: "Boulder, CO",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["climate science", "environmental science", "research"],
    description: "Participate in research related to climate change, weather prediction, and environmental monitoring.",
    url: "https://www.noaa.gov/office-education/opportunities"
  },
  {
    id: 21,
    title: "Remote Software Engineering Intern",
    company: "Twitter",
    location: "Remote",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["software engineering", "web development", "computer science"],
    description: "Work remotely on Twitter's platform and learn about scaling technology to millions of users.",
    url: "https://careers.twitter.com/en/university.html"
  },
  {
    id: 22,
    title: "Game Development Internship",
    company: "Electronic Arts",
    location: "Redwood City, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["game development", "software engineering", "3D graphics"],
    description: "Gain experience in game development and contribute to popular EA titles.",
    url: "https://www.ea.com/careers/students"
  },
  {
    id: 23,
    title: "Artificial Intelligence Researcher",
    company: "OpenAI",
    location: "San Francisco, CA",
    type: "job",
    educationLevel: ["graduate", "phd"],
    field: ["AI", "machine learning", "computer science"],
    description: "Research and develop cutting-edge AI technologies that have a positive impact on society.",
    url: "https://openai.com/careers"
  },
  {
    id: 24,
    title: "Virtual Reality Intern",
    company: "Meta",
    location: "Menlo Park, CA",
    type: "internship",
    educationLevel: ["college", "undergraduate", "graduate"],
    field: ["VR/AR", "software engineering", "3D design"],
    description: "Help build the future of virtual reality experiences and metaverse technologies.",
    url: "https://www.metacareers.com/students-and-grads"
  }
];

// Education level options
const EDUCATION_LEVELS = [
  { value: "high school", label: "High School Student" },
  { value: "high school graduate", label: "High School Graduate" },
  { value: "college", label: "College Student" },
  { value: "undergraduate", label: "Undergraduate" },
  { value: "graduate", label: "Graduate Student" },
  { value: "bootcamp", label: "Bootcamp" },
  { value: "phd", label: "PhD Student" }
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
  "Biology",
  "Cybersecurity",
  "Mobile Development",
  "Game Development",
  "Design",
  "UI/UX",
  "Robotics",
  "VR/AR",
  "Environmental Science",
  "Healthcare",
  "Journalism"
];

// Extract unique locations from opportunities
const LOCATIONS = ["All Locations", "Remote", ...Array.from(new Set(
  SAMPLE_OPPORTUNITIES.map(opp => opp.location)
  .filter(location => location !== "Remote" && location !== "Various Locations")
))].sort();

function Opportunities() {
  const [location, setLocation] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [field, setField] = useState('');
  const [showResults, setShowResults] = useState(false);
  
  // Filter opportunities based on search criteria
  const filteredOpportunities = SAMPLE_OPPORTUNITIES.filter(opportunity => {
    const locationMatch = !location || location === "All Locations" || 
      opportunity.location === location || 
      (location === "Remote" && opportunity.location === "Remote");
    
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
  
  // Function to handle Apply button click
  const handleApply = (url) => {
    window.open(url, '_blank');
  };
  
  return (
    <div className="opportunities-page">
      <div className="background-square"></div>
      
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">🧠 Forge Future</div>
        <div className="navbar-links">
          <Link to="/essay-aid" className="nav-link">College Essay Aid</Link>
          <Link to="/opportunities" className="nav-link active">Internship/Job Opportunities</Link>
          <Link to="/" className="nav-link">Interview AI</Link>
        </div>
      </nav>
      
      <div className="opportunities-container">
        <h1 style={{ color: '#7e57c2' }}>🧠 Find Internships & Job Opportunities</h1>
        <p className="subtitle">Discover opportunities that match your location, education level, and interests</p>
        
        <div className="search-section">
          <form onSubmit={handleSearch}>
            <div className="search-filters">
              <div className="filter-group">
                <label htmlFor="location">Location</label>
                <select 
                  id="location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                >
                  <option value="">All Locations</option>
                  {LOCATIONS.map(loc => (
                    <option key={loc} value={loc}>{loc}</option>
                  ))}
                </select>
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
                    <button 
                      className="apply-button"
                      onClick={() => handleApply(opportunity.url)}
                    >
                      Apply Now
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        <div className="opportunities-info">
          <h2>Resources to Help Your Career</h2>
          <div className="info-cards">
            <div className="info-card">
              <h3>Resume Building</h3>
              <p>A strong resume is essential for landing internships and jobs. Highlight relevant coursework, projects, and skills that match the position you're applying for.</p>
              <p><a href="https://www.indeed.com/career-advice/resumes-cover-letters/student-resume" target="_blank" rel="noopener noreferrer">Learn more about creating an effective resume →</a></p>
            </div>
            
            <div className="info-card">
              <h3>Interview Preparation</h3>
              <p>Practice answering common interview questions and research the company before your interview. Prepare examples that showcase your skills and experiences.</p>
              <p><a href="https://www.themuse.com/advice/interview-questions-and-answers" target="_blank" rel="noopener noreferrer">Learn more about interview techniques →</a></p>
            </div>
            
            <div className="info-card">
              <h3>Networking</h3>
              <p>Building a professional network can help you discover opportunities and get referrals. Attend career fairs, join industry-related clubs, and connect with professionals on LinkedIn.</p>
              <p><a href="https://www.linkedin.com/learning/topics/career-development" target="_blank" rel="noopener noreferrer">Learn more about networking strategies →</a></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Opportunities; 