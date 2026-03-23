import React, { useState, useRef, useEffect } from "react";
import type { MenuItem } from "../types";

interface MenuItemPickerProps {
  selectedIds: string[];
  menuItems: MenuItem[];
  onChange: (ids: string[]) => void;
  disabled?: boolean;
}

const containerStyle: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 6,
  alignItems: "flex-start",
  position: "relative",
};

const chipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 4,
  background: "var(--dpz-surface-elevated)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "3px 8px",
  fontSize: 12,
  color: "var(--text-primary)",
};

const chipRemoveStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "var(--text-secondary)",
  cursor: "pointer",
  padding: 0,
  fontSize: 14,
  lineHeight: 1,
  display: "flex",
  alignItems: "center",
};

const addBtnStyle: React.CSSProperties = {
  background: "var(--dpz-surface-elevated)",
  border: "1px dashed var(--border-default)",
  borderRadius: 4,
  padding: "3px 10px",
  fontSize: 12,
  color: "var(--text-secondary)",
  cursor: "pointer",
  fontFamily: "var(--font-family)",
};

const dropdownStyle: React.CSSProperties = {
  position: "absolute",
  top: "calc(100% + 4px)",
  left: 0,
  zIndex: 200,
  background: "var(--dpz-surface-elevated)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  minWidth: 240,
  maxHeight: 260,
  overflowY: "auto",
  boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
};

const dropdownGroupLabelStyle: React.CSSProperties = {
  padding: "6px 10px 2px",
  fontSize: 10,
  fontWeight: 700,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};

const dropdownItemStyle: React.CSSProperties = {
  padding: "7px 12px",
  fontSize: 13,
  color: "var(--text-primary)",
  cursor: "pointer",
};

const MenuItemPicker: React.FC<MenuItemPickerProps> = ({
  selectedIds,
  menuItems,
  onChange,
  disabled = false,
}) => {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const selectedItems = menuItems.filter((m) => selectedIds.includes(m.item_id));
  const availableItems = menuItems.filter((m) => !selectedIds.includes(m.item_id));

  // Group available items by category
  const grouped: Record<string, MenuItem[]> = {};
  for (const item of availableItems) {
    const cat = item.category || "Other";
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  }

  const handleRemove = (id: string) => {
    onChange(selectedIds.filter((x) => x !== id));
  };

  const handleAdd = (id: string) => {
    onChange([...selectedIds, id]);
    setOpen(false);
  };

  return (
    <div style={containerStyle} ref={dropdownRef}>
      {selectedItems.map((item) => (
        <span key={item.item_id} style={chipStyle}>
          {item.name}
          {!disabled && (
            <button
              style={chipRemoveStyle}
              onClick={() => handleRemove(item.item_id)}
              title={`Remove ${item.name}`}
              type="button"
            >
              ×
            </button>
          )}
        </span>
      ))}

      {!disabled && (
        <button
          style={addBtnStyle}
          onClick={() => setOpen((v) => !v)}
          type="button"
          disabled={availableItems.length === 0}
        >
          + Add Item
        </button>
      )}

      {open && availableItems.length > 0 && (
        <div style={dropdownStyle}>
          {Object.entries(grouped).map(([cat, items]) => (
            <React.Fragment key={cat}>
              <div style={dropdownGroupLabelStyle}>{cat}</div>
              {items.map((item) => (
                <div
                  key={item.item_id}
                  style={dropdownItemStyle}
                  onClick={() => handleAdd(item.item_id)}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLDivElement).style.background =
                      "var(--dpz-surface)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLDivElement).style.background =
                      "transparent";
                  }}
                  role="option"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleAdd(item.item_id);
                  }}
                >
                  {item.name}
                </div>
              ))}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
};

export default MenuItemPicker;
