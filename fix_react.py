import re

path = r'c:\Users\Lenovo\major_project\frontend\src\pages\AddPersonPage.jsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r"  // ── render helpers ──.*?  \);\n",
    "",
    content,
    flags=re.DOTALL
)

helpers = """
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

"""

if "// ── render helpers" not in content:
    content = content.replace("export default function AddPersonPage() {", helpers + "export default function AddPersonPage() {")

    content = content.replace('<Input name=', '<Input formData={formData} handleChange={handleChange} errors={errors} name=')
    content = content.replace('<Select name=', '<Select formData={formData} handleChange={handleChange} errors={errors} name=')
    content = content.replace('<Textarea name=', '<Textarea formData={formData} handleChange={handleChange} name=')
    content = content.replace('<Field label=', '<Field errors={errors} label=')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied.")
else:
    print("Already applied?")
