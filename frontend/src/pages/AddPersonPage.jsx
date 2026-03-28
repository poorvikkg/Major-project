import { useState } from 'react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

export default function AddPersonPage() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    description: '',
  });
  const [photo, setPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const { user } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPhoto(file);
      const reader = new FileReader();
      reader.onloadend = () => setPhotoPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.age) newErrors.age = 'Age is required';
    else if (isNaN(formData.age) || formData.age < 0 || formData.age > 150) newErrors.age = 'Enter a valid age';
    if (!formData.gender) newErrors.gender = 'Gender is required';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    
    const formDataObj = new FormData();
    formDataObj.append('name', formData.name);
    formDataObj.append('age', formData.age);
    formDataObj.append('gender', formData.gender);
    formDataObj.append('description', formData.description);
    if (photo) {
      formDataObj.append('image', photo);
    }

    try {
      const response = await fetch('http://localhost:8000/api/add-person', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`
        },
        body: formDataObj,
      });
      
      const data = await response.json();
      setIsSubmitting(false);

      if (response.ok && data.status === 'success') {
        setSubmitSuccess(true);
        // Reset form after success
        setTimeout(() => {
          setFormData({ name: '', age: '', gender: '', description: '' });
          setPhoto(null);
          setPhotoPreview(null);
          setSubmitSuccess(false);
        }, 3000);
      } else {
        setErrors({ submit: data.message || 'Failed to add person. Are you sure you are logged in as admin?' });
      }
    } catch (err) {
      setIsSubmitting(false);
      setErrors({ submit: 'Network error occurred. Please try again later.' });
    }
  };

  return (
    <div className="add-person-page" id="add-person-page">
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <div className="page-header-icon primary">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="16" cy="12" r="5" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M6 28C6 22.5 10.5 18 16 18C21.5 18 26 22.5 26 28" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none"/>
              <circle cx="24" cy="24" r="6" fill="var(--color-primary)"/>
              <path d="M24 21V27M21 24H27" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Add Missing Person</h1>
            <p className="page-subtitle">Register a new case by providing the person's details and photograph.</p>
          </div>
        </div>

        {submitSuccess && (
          <div className="alert alert-success fade-in" id="submit-success">
            <span className="alert-icon">✓</span>
            Missing person record has been successfully created!
          </div>
        )}

        {errors.submit && (
          <div className="alert alert-error" style={{marginBottom: "1rem"}}>
            <span className="alert-icon">⚠</span>
            {errors.submit}
          </div>
        )}

        <form onSubmit={handleSubmit} className="form-card" id="add-person-form">
          <div className="form-grid">
            {/* Photo Upload Section */}
            <div className="form-section photo-section">
              <h2 className="section-title">Photograph</h2>
              <label htmlFor="photo-upload" className="photo-upload-area" id="photo-upload-label">
                {photoPreview ? (
                  <img src={photoPreview} alt="Preview" className="photo-preview" />
                ) : (
                  <div className="photo-placeholder">
                    <svg viewBox="0 0 48 48" fill="none" width="48" height="48">
                      <rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.4"/>
                      <circle cx="18" cy="22" r="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.4"/>
                      <path d="M6 34L16 24L26 34L34 26L42 34" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.4"/>
                    </svg>
                    <p>Click to upload photo</p>
                    <span>JPG, PNG up to 5MB</span>
                  </div>
                )}
                <input 
                  type="file" 
                  id="photo-upload" 
                  accept="image/*" 
                  onChange={handlePhotoChange}
                  style={{ display: 'none' }}
                />
              </label>
            </div>

            {/* Details Section */}
            <div className="form-section details-section">
              <h2 className="section-title">Personal Details</h2>

              <div className="form-group">
                <label htmlFor="name" className="form-label">Full Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  className={`form-input ${errors.name ? 'error' : ''}`}
                  placeholder="Enter full name"
                  value={formData.name}
                  onChange={handleChange}
                />
                {errors.name && <span className="form-error">{errors.name}</span>}
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="age" className="form-label">Age</label>
                  <input
                    type="number"
                    id="age"
                    name="age"
                    className={`form-input ${errors.age ? 'error' : ''}`}
                    placeholder="Enter age"
                    value={formData.age}
                    onChange={handleChange}
                    min="0"
                    max="150"
                  />
                  {errors.age && <span className="form-error">{errors.age}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="gender" className="form-label">Gender</label>
                  <select
                    id="gender"
                    name="gender"
                    className={`form-input form-select ${errors.gender ? 'error' : ''}`}
                    value={formData.gender}
                    onChange={handleChange}
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                  {errors.gender && <span className="form-error">{errors.gender}</span>}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="description" className="form-label">Description</label>
                <textarea
                  id="description"
                  name="description"
                  className={`form-input form-textarea ${errors.description ? 'error' : ''}`}
                  placeholder="Physical description, last seen wearing, distinguishing features..."
                  value={formData.description}
                  onChange={handleChange}
                  rows="4"
                />
                {errors.description && <span className="form-error">{errors.description}</span>}
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setFormData({ name: '', age: '', gender: '', description: '' });
                setPhoto(null);
                setPhotoPreview(null);
                setErrors({});
              }}
              id="reset-form-btn"
            >
              Reset
            </button>
            <button
              type="submit"
              className={`btn btn-primary ${isSubmitting ? 'loading' : ''}`}
              disabled={isSubmitting}
              id="submit-person-btn"
            >
              {isSubmitting ? <span className="btn-loader"></span> : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
