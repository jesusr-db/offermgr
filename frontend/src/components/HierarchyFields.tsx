import React from "react";
import type { HierarchyValues } from "../types";

interface HierarchyValues6 {
  h1_org_scope: string;
  h2_org_scope: string;
  h3_org_scope: string;
  h4_loyalty_type: string;
  h5_discount_type: string;
  h6_item_structure: string;
}

interface HierarchyFieldsProps {
  values: HierarchyValues6;
  hierarchyValues: HierarchyValues;
  onChange: (field: string, value: string) => void;
  disabled?: boolean;
}

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr 1fr",
  gap: "10px 16px",
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
};

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.4px",
};

const selectStyle: React.CSSProperties = {
  background: "var(--dpz-surface-elevated)",
  color: "var(--text-primary)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "5px 8px",
  fontSize: 13,
  cursor: "pointer",
  outline: "none",
  fontFamily: "var(--font-family)",
  width: "100%",
};

const disabledSelectStyle: React.CSSProperties = {
  ...selectStyle,
  opacity: 0.5,
  cursor: "not-allowed",
};

const FIELDS: Array<{
  key: keyof HierarchyValues6;
  label: string;
  optionsKey: keyof HierarchyValues;
}> = [
  { key: "h1_org_scope", label: "Org Scope (H1)", optionsKey: "h1_org_scope" },
  { key: "h2_org_scope", label: "Org Scope (H2)", optionsKey: "h2_org_scope" },
  { key: "h3_org_scope", label: "Org Scope (H3)", optionsKey: "h3_org_scope" },
  { key: "h4_loyalty_type", label: "Loyalty Type (H4)", optionsKey: "h4_loyalty_type" },
  { key: "h5_discount_type", label: "Discount Type (H5)", optionsKey: "h5_discount_type" },
  { key: "h6_item_structure", label: "Item Structure (H6)", optionsKey: "h6_item_structure" },
];

const HierarchyFields: React.FC<HierarchyFieldsProps> = ({
  values,
  hierarchyValues,
  onChange,
  disabled = false,
}) => {
  return (
    <div style={gridStyle}>
      {FIELDS.map(({ key, label, optionsKey }) => (
        <div key={key} style={fieldStyle}>
          <label style={labelStyle}>{label}</label>
          <select
            style={disabled ? disabledSelectStyle : selectStyle}
            value={values[key]}
            disabled={disabled}
            onChange={(e) => onChange(key, e.target.value)}
          >
            <option value="">— Select —</option>
            {hierarchyValues[optionsKey].map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
};

export default HierarchyFields;
