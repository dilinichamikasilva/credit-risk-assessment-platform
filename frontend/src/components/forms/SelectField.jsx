export default function SelectField({
  label,
  name,
  value,
  onChange,
  options,
  required = true,
}) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <select
        id={name}
        name={name}
        value={value}
        required={required}
        onChange={(e) => onChange(name, e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
