import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

const SECTIONS = [
  { id: 'personal',    label: 'Personal Details',       icon: '' },
  { id: 'physical',   label: 'Physical Identification', icon: '' },
  { id: 'lastseen',   label: 'Last Seen Details',       icon: '' },
  { id: 'additional', label: 'Additional Info',         icon: '' },
  { id: 'complainant',label: 'Complainant Details',     icon: '' },
  { id: 'images',     label: 'Photographs',             icon: '' },
];

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'];
const COMPLEXIONS = ['Fair', 'Wheatish', 'Dusky', 'Dark', 'Very Dark'];
const FACE_SHAPES = ['Oval', 'Round', 'Square', 'Heart', 'Diamond', 'Oblong', 'Triangle'];
const HAIR_COLORS = ['Black', 'Dark Brown', 'Brown', 'Blonde', 'Red', 'Grey', 'White', 'Bald', 'Other'];
const EYE_COLORS  = ['Black', 'Dark Brown', 'Brown', 'Hazel', 'Green', 'Blue', 'Grey', 'Other'];

const emptyForm = {
  // A - Personal
  name: '', nickname: '', age: '', gender: '',
  date_of_birth: '', height: '', weight: '', complexion: '',
  blood_group: '', nationality: 'Indian',
  // B - Physical
  identification_marks: '', face_shape: '', hair_color: '',
  eye_color: '', beard_mustache: '',
  has_disability: false, disability_details: '',
  // C - Last Seen
  last_seen_location: '', last_seen_date: '', last_seen_time: '',
  last_seen_wearing: '', accompanied_by: '', suspected_location: '',
  // D - Additional
  occupation: '', habits: '', languages_known: '',
  medical_conditions: '', behavioral_notes: '', description: '',
  // E - Complainant
  complainant_name: '', complainant_phone: '', complainant_alt_phone: '',
  complainant_email: '', complainant_address: '', complainant_relation: '',
};


// ── render helpers ────────────────────────────────────────────────────────
const Field = ({ label, name, required, errors, children }) => (
  <div className="ap-field">
    <label className="ap-label">{label}{required && <span className="ap-required">*</span>}</label>
    {children}
    {errors?.[name] && <span className="ap-error">{errors[name]}</span>}
  </div>
);

const Input = ({ name, type = 'text', placeholder, required, formData, handleChange, errors, ...rest }) => (
  <input
    type={type} name={name} id={name}
    className={`form-input${errors?.[name] ? ' error' : ''}`}
    placeholder={placeholder}
    value={formData?.[name] || ''}
    onChange={handleChange}
    required={required}
    {...rest}
  />
);

const Select = ({ name, required, formData, handleChange, errors, children }) => (
  <select
    name={name} id={name}
    className={`form-input form-select${errors?.[name] ? ' error' : ''}`}
    value={formData?.[name] || ''}
    onChange={handleChange}
    required={required}
  >{children}</select>
);

const Textarea = ({ name, placeholder, rows = 3, formData, handleChange }) => (
  <textarea
    name={name} id={name}
    className="form-input form-textarea"
    placeholder={placeholder}
    value={formData?.[name] || ''}
    onChange={handleChange}
    rows={rows}
  />
);

export default function AddPersonPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [activeSection, setActiveSection] = useState('personal');
  const [formData, setFormData] = useState(emptyForm);
  const [photos, setPhotos]     = useState([]);
  const [previews, setPreviews] = useState([]);
  const [errors, setErrors]     = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError]   = useState('');

  // ── handlers ──────────────────────────────────────────────────────────────
  const set = (field, value) => {
    setFormData(p => ({ ...p, [field]: value }));
    if (errors[field]) setErrors(p => ({ ...p, [field]: '' }));
  };

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    set(name, type === 'checkbox' ? checked : value);
  };

  const handleFiles = e => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    const remaining = 10 - photos.length;
    const toAdd = files.slice(0, remaining);
    setPhotos(p => [...p, ...toAdd]);
    toAdd.forEach(f => {
      const reader = new FileReader();
      reader.onloadend = () => setPreviews(p => [...p, reader.result]);
      reader.readAsDataURL(f);
    });
    e.target.value = '';
  };

  const removePhoto = idx => {
    setPhotos(p => p.filter((_, i) => i !== idx));
    setPreviews(p => p.filter((_, i) => i !== idx));
  };

  // ── validation ────────────────────────────────────────────────────────────
  const validate = () => {
    const errs = {};
    if (!formData.name.trim())  errs.name   = 'Full name is required';
    if (!formData.age)          errs.age    = 'Age is required';
    else if (+formData.age < 0 || +formData.age > 150) errs.age = 'Enter a valid age (0–150)';
    if (!formData.gender)       errs.gender = 'Gender is required';
    if (!formData.last_seen_location.trim()) errs.last_seen_location = 'Last seen location is required';
    if (!formData.complainant_name.trim())   errs.complainant_name   = 'Complainant name is required';
    if (!formData.complainant_phone.trim())  errs.complainant_phone  = 'Phone number is required';
    if (photos.length === 0)    errs.photos = 'At least one photograph is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // ── submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async e => {
    e.preventDefault();
    if (!validate()) {
      // Jump to first errored section
      const sectionFields = {
        personal: ['name','age','gender'],
        lastseen: ['last_seen_location'],
        complainant: ['complainant_name','complainant_phone'],
        images: ['photos'],
      };
      for (const [sec, fields] of Object.entries(sectionFields)) {
        if (fields.some(f => errors[f])) { setActiveSection(sec); break; }
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError('');

    const fd = new FormData();
    Object.entries(formData).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') fd.append(k, v);
    });
    photos.forEach(p => fd.append('images', p));

    try {
      const res  = await fetch('http://localhost:8000/api/add-person', {
        method: 'POST',
        headers: { Authorization: `Bearer ${user?.token}` },
        body: fd,
      });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        setSubmitSuccess(true);
        setTimeout(() => {
          navigate('/missing-persons');
        }, 2000);
      } else {
        setSubmitError(data.message || 'Failed to add person. Check your login status.');
      }
    } catch {
      setSubmitError('Network error. Please check the backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData(emptyForm);
    setPhotos([]); setPreviews([]);
    setErrors({}); setSubmitError('');
    setActiveSection('personal');
  };

  // ── section nav ───────────────────────────────────────────────────────────
  const sectionIdx  = SECTIONS.findIndex(s => s.id === activeSection);
  const goNext = () => setActiveSection(SECTIONS[Math.min(sectionIdx + 1, SECTIONS.length - 1)].id);
  const goPrev = () => setActiveSection(SECTIONS[Math.max(sectionIdx - 1, 0)].id);



  return (
    <div className="ap-page" id="add-person-page">
      <Navbar />
      <div className="page-container ap-container">

        {/* Header */}
        <div className="ap-header">
          <div className="ap-header-icon">
            <svg viewBox="0 0 32 32" fill="none" width="24" height="24">
              <circle cx="16" cy="12" r="5" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M6 28C6 22.5 10.5 18 16 18C21.5 18 26 22.5 26 28" stroke="currentColor" strokeWidth="2" strokeLinecap="round" fill="none"/>
              <circle cx="24" cy="24" r="6" fill="var(--color-accent)"/>
              <path d="M24 21V27M21 24H27" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <h1 className="page-title">Register Missing Person</h1>
            <p className="page-subtitle">Complete the FIR-level report across all sections below.</p>
          </div>
        </div>

        {/* Alerts */}
        {submitSuccess && (
          <div className="alert alert-success fade-in">
            <span className="alert-icon"></span>
            Record created successfully! Redirecting to persons list…
          </div>
        )}
        {submitError && (
          <div className="alert alert-error">
            <span className="alert-icon"></span>
            {submitError}
          </div>
        )}

        {/* Section Tabs */}
        <div className="ap-tabs" role="tablist">
          {SECTIONS.map((s, i) => {
            const hasErr = (
              (s.id === 'personal'    && (errors.name || errors.age || errors.gender)) ||
              (s.id === 'lastseen'    && errors.last_seen_location) ||
              (s.id === 'complainant' && (errors.complainant_name || errors.complainant_phone)) ||
              (s.id === 'images'      && errors.photos)
            );
            return (
              <button
                key={s.id}
                type="button"
                role="tab"
                className={`ap-tab${activeSection === s.id ? ' active' : ''}${hasErr ? ' has-error' : ''}`}
                onClick={() => setActiveSection(s.id)}
                id={`tab-${s.id}`}
              >
                <span className="ap-tab-icon">{s.icon}</span>
                <span className="ap-tab-num">{i + 1}</span>
                <span className="ap-tab-label">{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} id="add-person-form" noValidate>
          <div className="ap-card">

            {/* ── A. Personal Details ──────────────────────────────── */}
            {activeSection === 'personal' && (
              <div className="ap-section" id="section-personal">
                <h2 className="ap-section-title"><span></span> Personal Details</h2>
                <div className="ap-grid-3">
                  <Field errors={errors} label="Full Name" name="name" required>
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="name" placeholder="Enter full legal name" required />
                  </Field>
                  <Field errors={errors} label="Nickname / Alias" name="nickname">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="nickname" placeholder="Any known alias" />
                  </Field>
                  <Field errors={errors} label="Nationality" name="nationality">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="nationality" placeholder="e.g. Indian" />
                  </Field>
                </div>
                <div className="ap-grid-3">
                  <Field errors={errors} label="Age" name="age" required>
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="age" type="number" placeholder="Age" min="0" max="150" required />
                  </Field>
                  <Field errors={errors} label="Gender" name="gender" required>
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="gender" required>
                      <option value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </Select>
                  </Field>
                  <Field errors={errors} label="Date of Birth" name="date_of_birth">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="date_of_birth" type="date" />
                  </Field>
                </div>
                <div className="ap-grid-3">
                  <Field errors={errors} label="Height" name="height">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="height" placeholder="e.g. 5ft 8in or 173cm" />
                  </Field>
                  <Field errors={errors} label="Weight" name="weight">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="weight" placeholder="e.g. 65kg" />
                  </Field>
                  <Field errors={errors} label="Blood Group" name="blood_group">
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="blood_group">
                      <option value="">Select blood group</option>
                      {BLOOD_GROUPS.map(b => <option key={b} value={b}>{b}</option>)}
                    </Select>
                  </Field>
                </div>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Complexion" name="complexion">
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="complexion">
                      <option value="">Select complexion</option>
                      {COMPLEXIONS.map(c => <option key={c} value={c}>{c}</option>)}
                    </Select>
                  </Field>
                </div>
              </div>
            )}

            {/* ── B. Physical Identification ───────────────────────── */}
            {activeSection === 'physical' && (
              <div className="ap-section" id="section-physical">
                <h2 className="ap-section-title"><span></span> Physical Identification</h2>
                <div className="ap-grid-3">
                  <Field errors={errors} label="Face Shape" name="face_shape">
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="face_shape">
                      <option value="">Select face shape</option>
                      {FACE_SHAPES.map(f => <option key={f} value={f}>{f}</option>)}
                    </Select>
                  </Field>
                  <Field errors={errors} label="Hair Color" name="hair_color">
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="hair_color">
                      <option value="">Select hair color</option>
                      {HAIR_COLORS.map(h => <option key={h} value={h}>{h}</option>)}
                    </Select>
                  </Field>
                  <Field errors={errors} label="Eye Color" name="eye_color">
                    <Select formData={formData} handleChange={handleChange} errors={errors} name="eye_color">
                      <option value="">Select eye color</option>
                      {EYE_COLORS.map(e => <option key={e} value={e}>{e}</option>)}
                    </Select>
                  </Field>
                </div>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Beard / Moustache" name="beard_mustache">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="beard_mustache" placeholder="e.g. Clean-shaven, Thick beard, Thin moustache" />
                  </Field>
                </div>
                <Field errors={errors} label="Identification Marks" name="identification_marks">
                  <Textarea formData={formData} handleChange={handleChange} name="identification_marks" placeholder="Describe any scars, tattoos, birthmarks, moles or other distinguishing marks with their locations..." rows={3} />
                </Field>
                <div className="ap-disability-row">
                  <label className="ap-checkbox-label">
                    <input
                      type="checkbox"
                      name="has_disability"
                      id="has_disability"
                      checked={formData.has_disability}
                      onChange={handleChange}
                      className="ap-checkbox"
                    />
                    <span>Person has a disability or physical condition</span>
                  </label>
                </div>
                {formData.has_disability && (
                  <Field errors={errors} label="Disability Details" name="disability_details">
                    <Textarea formData={formData} handleChange={handleChange} name="disability_details" placeholder="Describe the disability or physical condition in detail..." rows={2} />
                  </Field>
                )}
              </div>
            )}

            {/* ── C. Last Seen Details ─────────────────────────────── */}
            {activeSection === 'lastseen' && (
              <div className="ap-section" id="section-lastseen">
                <h2 className="ap-section-title"><span></span> Last Seen Details</h2>
                <Field errors={errors} label="Last Seen Location" name="last_seen_location" required>
                  <Textarea formData={formData} handleChange={handleChange} name="last_seen_location" placeholder="Full address or description of where the person was last seen..." rows={2} />
                  {errors.last_seen_location && <span className="ap-error">{errors.last_seen_location}</span>}
                </Field>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Last Seen Date" name="last_seen_date">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="last_seen_date" type="date" />
                  </Field>
                  <Field errors={errors} label="Last Seen Time" name="last_seen_time">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="last_seen_time" type="time" />
                  </Field>
                </div>
                <Field errors={errors} label="Clothing Description" name="last_seen_wearing">
                  <Textarea formData={formData} handleChange={handleChange} name="last_seen_wearing" placeholder="Describe what the person was wearing at the time of disappearance (colour, style, footwear)..." rows={2} />
                </Field>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Accompanied By" name="accompanied_by">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="accompanied_by" placeholder="Name(s) or description of anyone with them" />
                  </Field>
                  <Field errors={errors} label="Suspected Location" name="suspected_location">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="suspected_location" placeholder="Any suspected area / destination" />
                  </Field>
                </div>
              </div>
            )}

            {/* ── D. Additional Information ────────────────────────── */}
            {activeSection === 'additional' && (
              <div className="ap-section" id="section-additional">
                <h2 className="ap-section-title"><span></span> Additional Information</h2>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Occupation" name="occupation">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="occupation" placeholder="e.g. Student, Farmer, Engineer" />
                  </Field>
                  <Field errors={errors} label="Languages Known" name="languages_known">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="languages_known" placeholder="e.g. Hindi, English, Tamil" />
                  </Field>
                </div>
                <Field errors={errors} label="Habits" name="habits">
                  <Textarea formData={formData} handleChange={handleChange} name="habits" placeholder="Any known habits — smoking, alcohol, substance use, frequents specific places..." rows={2} />
                </Field>
                <Field errors={errors} label="Medical Conditions" name="medical_conditions">
                  <Textarea formData={formData} handleChange={handleChange} name="medical_conditions" placeholder="Known illnesses, medications, allergies, or psychiatric conditions..." rows={2} />
                </Field>
                <Field errors={errors} label="Behavioural Notes" name="behavioral_notes">
                  <Textarea formData={formData} handleChange={handleChange} name="behavioral_notes" placeholder="Personality traits, tendencies, past incidents, social behaviour..." rows={2} />
                </Field>
                <Field errors={errors} label="General Description / Remarks" name="description">
                  <Textarea formData={formData} handleChange={handleChange} name="description" placeholder="Any additional notes or information relevant to this case..." rows={2} />
                </Field>
              </div>
            )}

            {/* ── E. Complainant Details ───────────────────────────── */}
            {activeSection === 'complainant' && (
              <div className="ap-section" id="section-complainant">
                <h2 className="ap-section-title"><span></span> Complainant Details</h2>
                <p className="ap-section-hint">Information about the person filing this report.</p>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Full Name" name="complainant_name" required>
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="complainant_name" placeholder="Complainant's full name" required />
                  </Field>
                  <Field errors={errors} label="Relation to Missing Person" name="complainant_relation">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="complainant_relation" placeholder="e.g. Father, Mother, Sibling, Friend" />
                  </Field>
                </div>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Phone Number" name="complainant_phone" required>
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="complainant_phone" type="tel" placeholder="Primary contact number" required />
                  </Field>
                  <Field errors={errors} label="Alternate Phone" name="complainant_alt_phone">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="complainant_alt_phone" type="tel" placeholder="Secondary contact number" />
                  </Field>
                </div>
                <div className="ap-grid-2">
                  <Field errors={errors} label="Email Address" name="complainant_email">
                    <Input formData={formData} handleChange={handleChange} errors={errors} name="complainant_email" type="email" placeholder="Email address (optional)" />
                  </Field>
                </div>
                <Field errors={errors} label="Address" name="complainant_address">
                  <Textarea formData={formData} handleChange={handleChange} name="complainant_address" placeholder="Full residential address of the complainant..." rows={2} />
                </Field>
              </div>
            )}

            {/* ── F. Photographs ───────────────────────────────────── */}
            {activeSection === 'images' && (
              <div className="ap-section" id="section-images">
                <h2 className="ap-section-title"><span></span> Photographs</h2>
                <p className="ap-section-hint">Upload 1–10 clear face photographs. Multiple images improve face recognition accuracy.</p>

                {errors.photos && (
                  <div className="alert alert-error" style={{marginBottom:'1rem'}}>
                    <span className="alert-icon"></span>{errors.photos}
                  </div>
                )}

                {/* Upload button */}
                {photos.length < 10 && (
                  <label className="ap-upload-zone" htmlFor="photo-input" id="photo-upload-label">
                    <svg viewBox="0 0 48 48" fill="none" width="40" height="40">
                      <rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.5"/>
                      <circle cx="18" cy="22" r="4" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.5"/>
                      <path d="M6 34L16 24L26 34L34 26L42 34" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.5"/>
                      <circle cx="36" cy="14" r="8" fill="var(--color-accent)"/>
                      <path d="M36 10V18M32 14H40" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
                    </svg>
                    <p className="ap-upload-title">Click to add photographs</p>
                    <p className="ap-upload-hint">JPG, PNG — up to 10 photos ({photos.length}/10 uploaded)</p>
                    <input
                      ref={fileRef}
                      type="file"
                      id="photo-input"
                      accept="image/*"
                      multiple
                      onChange={handleFiles}
                      style={{ display: 'none' }}
                    />
                  </label>
                )}

                {/* Thumbnail grid */}
                {previews.length > 0 && (
                  <div className="ap-thumbs-grid">
                    {previews.map((src, i) => (
                      <div key={i} className="ap-thumb" id={`thumb-${i}`}>
                        <img src={src} alt={`Photo ${i + 1}`} className="ap-thumb-img" />
                        <div className="ap-thumb-overlay">
                          <button
                            type="button"
                            className="ap-thumb-remove"
                            onClick={() => removePhoto(i)}
                            title="Remove photo"
                            id={`remove-photo-${i}`}
                          ></button>
                        </div>
                        <span className="ap-thumb-num">{i + 1}</span>
                      </div>
                    ))}
                    {photos.length < 10 && (
                      <label className="ap-thumb ap-thumb-add" htmlFor="photo-input">
                        <span>+</span>
                        <small>Add more</small>
                      </label>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation / Actions */}
          <div className="ap-nav-bar">
            <div className="ap-nav-left">
              {sectionIdx > 0 && (
                <button type="button" className="btn btn-ghost" onClick={goPrev} id="btn-prev">
                  ← Previous
                </button>
              )}
            </div>
            <div className="ap-nav-right">
              <button type="button" className="btn btn-ghost" onClick={resetForm} id="btn-reset">
                Reset Form
              </button>
              {sectionIdx < SECTIONS.length - 1 ? (
                <button type="button" className="btn btn-primary" onClick={goNext} id="btn-next">
                  Next →
                </button>
              ) : (
                <button
                  type="submit"
                  className={`btn btn-primary btn-submit${isSubmitting ? ' loading' : ''}`}
                  disabled={isSubmitting}
                  id="submit-person-btn"
                >
                  {isSubmitting
                    ? <><span className="btn-loader" /> Submitting…</>
                    : ' Submit Report'}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
