export default function NumberField({
  label,
  name,
  value,
  onChange,
  min = 0,
  max,
  step = "any",
  slider = false,
  required = true,
}) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        type="number"
        name={name}
        value={value}
        min={min}
        max={max}
        step={step}
        required={required}
        onChange={(e) => onChange(name, e.target.value)}
      />
      {slider && max !== undefined && (
        <input
          type="range"
          min={min}
          max={max}
          step={step === "any" ? 0.01 : step}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
        />
      )}
    </div>
  );
}
