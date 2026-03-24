import React from "react";
import type { OfferFilters, HierarchyValues } from "../types";

interface FilterBarProps {
  filters: OfferFilters;
  hierarchyValues: HierarchyValues;
  offerCount: number;
  onFilterChange: (f: Partial<OfferFilters>) => void;
  onNewOffer: () => void;
}

const barStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 12px",
  background: "var(--dpz-surface)",
  borderBottom: "1px solid var(--border-default)",
  flexShrink: 0,
  flexWrap: "wrap",
};

const inputStyle: React.CSSProperties = {
  background: "var(--dpz-surface-elevated)",
  color: "var(--text-primary)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "5px 10px",
  fontSize: 13,
  outline: "none",
  fontFamily: "var(--font-family)",
  width: 210,
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
};

const newBtnStyle: React.CSSProperties = {
  marginLeft: "auto",
  background: "var(--dpz-blue)",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  padding: "5px 14px",
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "var(--font-family)",
  whiteSpace: "nowrap",
};

const countStyle: React.CSSProperties = {
  fontSize: 12,
  color: "var(--text-secondary)",
  whiteSpace: "nowrap",
  paddingLeft: 4,
};

const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  hierarchyValues,
  offerCount,
  onFilterChange,
  onNewOffer,
}) => {
  return (
    <div style={barStyle}>
      <input
        type="text"
        style={inputStyle}
        placeholder="Search by code or description"
        value={filters.search}
        onChange={(e) => onFilterChange({ search: e.target.value })}
      />

      <select
        style={selectStyle}
        value={filters.status}
        onChange={(e) => onFilterChange({ status: e.target.value })}
      >
        <option value="">All Statuses</option>
        <option value="draft">Draft</option>
        <option value="active">Active</option>
        <option value="expired">Expired</option>
      </select>

      <select
        style={selectStyle}
        value={filters.h4_loyalty_type}
        onChange={(e) => onFilterChange({ h4_loyalty_type: e.target.value })}
      >
        <option value="">All Loyalty Types</option>
        {hierarchyValues.h4_loyalty_type.map((v) => (
          <option key={v} value={v}>{v}</option>
        ))}
      </select>

      <select
        style={selectStyle}
        value={filters.h5_discount_type}
        onChange={(e) => onFilterChange({ h5_discount_type: e.target.value })}
      >
        <option value="">All Discount Types</option>
        {hierarchyValues.h5_discount_type.map((v) => (
          <option key={v} value={v}>{v}</option>
        ))}
      </select>

      <select
        style={selectStyle}
        value={filters.h6_item_structure}
        onChange={(e) => onFilterChange({ h6_item_structure: e.target.value })}
      >
        <option value="">All Item Structures</option>
        {hierarchyValues.h6_item_structure.map((v) => (
          <option key={v} value={v}>{v}</option>
        ))}
      </select>

      <select
        style={selectStyle}
        value={filters.h1_org_scope}
        onChange={(e) => onFilterChange({ h1_org_scope: e.target.value })}
      >
        <option value="">All Org Scopes</option>
        {hierarchyValues.h1_org_scope.map((v) => (
          <option key={v} value={v}>{v}</option>
        ))}
      </select>

      <span style={countStyle}>{offerCount} offers</span>

      <button style={newBtnStyle} onClick={onNewOffer}>
        + New Offer
      </button>
    </div>
  );
};

export default FilterBar;
