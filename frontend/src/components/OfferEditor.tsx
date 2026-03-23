import React, { useState, useEffect, useCallback } from "react";
import type { Offer, MenuItem, HierarchyValues } from "../types";
import HierarchyFields from "./HierarchyFields";
import MenuItemPicker from "./MenuItemPicker";

interface OfferEditorProps {
  offer: Offer | null;
  isNew: boolean;
  menuItems: MenuItem[];
  hierarchyValues: HierarchyValues;
  isLoading: boolean;
  onSave: (data: Partial<Offer> & { menu_item_ids?: string[] }) => Promise<void>;
  onReset: () => void;
  onMarkDirty: () => void;
}

interface FormState {
  coupon_code: string;
  description: string;
  status: "draft" | "active" | "expired";
  start_date: string;
  end_date: string;
  dollar_amount: string;
  h1_org_scope: string;
  h2_org_scope: string;
  h3_org_scope: string;
  h4_loyalty_type: string;
  h5_discount_type: string;
  h6_item_structure: string;
  menu_item_ids: string[];
}

function offerToForm(offer: Offer): FormState {
  return {
    coupon_code: offer.coupon_code,
    description: offer.description,
    status: offer.status,
    start_date: offer.start_date,
    end_date: offer.end_date,
    dollar_amount: offer.dollar_amount != null ? String(offer.dollar_amount) : "",
    h1_org_scope: offer.h1_org_scope,
    h2_org_scope: offer.h2_org_scope,
    h3_org_scope: offer.h3_org_scope,
    h4_loyalty_type: offer.h4_loyalty_type,
    h5_discount_type: offer.h5_discount_type,
    h6_item_structure: offer.h6_item_structure,
    menu_item_ids: offer.menu_items?.map((m) => m.item_id) ?? [],
  };
}

const emptyForm = (): FormState => ({
  coupon_code: "",
  description: "",
  status: "draft",
  start_date: "",
  end_date: "",
  dollar_amount: "",
  h1_org_scope: "",
  h2_org_scope: "",
  h3_org_scope: "",
  h4_loyalty_type: "",
  h5_discount_type: "",
  h6_item_structure: "",
  menu_item_ids: [],
});

// ---- Styles ----

const panelStyle: React.CSSProperties = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  background: "var(--dpz-dark)",
  overflow: "hidden",
};

const emptyPanelStyle: React.CSSProperties = {
  flex: 1,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "var(--text-muted)",
  fontSize: 14,
};

const headerStyle: React.CSSProperties = {
  padding: "14px 20px 12px",
  borderBottom: "1px solid var(--border-default)",
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexShrink: 0,
};

const titleStyle: React.CSSProperties = {
  fontSize: 16,
  fontWeight: 700,
  color: "var(--text-primary)",
  fontFamily: "var(--font-mono)",
  letterSpacing: "0.3px",
};

const scrollAreaStyle: React.CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "20px 24px",
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.6px",
  marginBottom: 10,
  marginTop: 20,
};

const sectionLabelFirstStyle: React.CSSProperties = {
  ...sectionLabelStyle,
  marginTop: 0,
};

const fieldRowStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr 1fr",
  gap: "10px 16px",
  marginBottom: 4,
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
};

const fieldLabelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.4px",
};

const inputStyle: React.CSSProperties = {
  background: "var(--dpz-surface-elevated)",
  color: "var(--text-primary)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "6px 10px",
  fontSize: 13,
  outline: "none",
  fontFamily: "var(--font-family)",
  width: "100%",
};

const monoInputStyle: React.CSSProperties = {
  ...inputStyle,
  fontFamily: "var(--font-mono)",
  letterSpacing: "0.3px",
};

const textareaStyle: React.CSSProperties = {
  ...inputStyle,
  resize: "vertical" as const,
  minHeight: 64,
};

const STATUS_COLORS: Record<string, string> = {
  active: "var(--status-active)",
  draft: "var(--status-draft)",
  expired: "var(--status-expired)",
};

const actionBarStyle: React.CSSProperties = {
  padding: "12px 24px",
  borderTop: "1px solid var(--border-default)",
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexShrink: 0,
  background: "var(--dpz-surface)",
};

const saveBtnStyle = (disabled: boolean): React.CSSProperties => ({
  background: disabled ? "var(--border-default)" : "var(--dpz-blue)",
  color: disabled ? "var(--text-muted)" : "#fff",
  border: "none",
  borderRadius: 4,
  padding: "6px 18px",
  fontSize: 13,
  fontWeight: 600,
  cursor: disabled ? "not-allowed" : "pointer",
  fontFamily: "var(--font-family)",
});

const resetBtnStyle: React.CSSProperties = {
  background: "transparent",
  color: "var(--text-secondary)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "6px 14px",
  fontSize: 13,
  cursor: "pointer",
  fontFamily: "var(--font-family)",
};

const transitionBtnStyle = (color: string): React.CSSProperties => ({
  marginLeft: "auto",
  background: color,
  color: "#fff",
  border: "none",
  borderRadius: 4,
  padding: "6px 16px",
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "var(--font-family)",
});

const savingOverlayStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  background: "rgba(26,26,26,0.7)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 50,
  fontSize: 14,
  color: "var(--text-secondary)",
};

// ---- Component ----

const OfferEditor: React.FC<OfferEditorProps> = ({
  offer,
  isNew,
  menuItems,
  hierarchyValues,
  isLoading,
  onSave,
  onReset,
  onMarkDirty,
}) => {
  const [form, setForm] = useState<FormState>(
    offer ? offerToForm(offer) : emptyForm()
  );
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Sync form when offer changes
  useEffect(() => {
    if (offer) {
      setForm(offerToForm(offer));
    } else if (isNew) {
      setForm(emptyForm());
    }
    setIsDirty(false);
  }, [offer, isNew]);

  const markDirty = useCallback(() => {
    if (!isDirty) {
      setIsDirty(true);
      onMarkDirty();
    }
  }, [isDirty, onMarkDirty]);

  const handleChange = useCallback(
    (field: keyof FormState, value: string | string[]) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      markDirty();
    },
    [markDirty]
  );

  const handleHierarchyChange = useCallback(
    (field: string, value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      markDirty();
    },
    [markDirty]
  );

  const handleMenuItemChange = useCallback(
    (ids: string[]) => {
      setForm((prev) => ({ ...prev, menu_item_ids: ids }));
      markDirty();
    },
    [markDirty]
  );

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload: Partial<Offer> & { menu_item_ids?: string[] } = {
        coupon_code: form.coupon_code,
        description: form.description,
        status: form.status,
        start_date: form.start_date,
        end_date: form.end_date,
        dollar_amount: form.dollar_amount !== "" ? Number(form.dollar_amount) : null,
        h1_org_scope: form.h1_org_scope,
        h2_org_scope: form.h2_org_scope,
        h3_org_scope: form.h3_org_scope,
        h4_loyalty_type: form.h4_loyalty_type,
        h5_discount_type: form.h5_discount_type,
        h6_item_structure: form.h6_item_structure,
        menu_item_ids: form.menu_item_ids,
      };
      await onSave(payload);
      setIsDirty(false);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (offer) {
      setForm(offerToForm(offer));
    } else {
      setForm(emptyForm());
    }
    setIsDirty(false);
    onReset();
  };

  const handleStatusTransition = async (newStatus: "active" | "expired") => {
    setIsSaving(true);
    try {
      const payload: Partial<Offer> & { menu_item_ids?: string[] } = {
        coupon_code: form.coupon_code,
        description: form.description,
        status: newStatus,
        start_date: form.start_date,
        end_date: form.end_date,
        dollar_amount: form.dollar_amount !== "" ? Number(form.dollar_amount) : null,
        h1_org_scope: form.h1_org_scope,
        h2_org_scope: form.h2_org_scope,
        h3_org_scope: form.h3_org_scope,
        h4_loyalty_type: form.h4_loyalty_type,
        h5_discount_type: form.h5_discount_type,
        h6_item_structure: form.h6_item_structure,
        menu_item_ids: form.menu_item_ids,
      };
      await onSave(payload);
      setIsDirty(false);
    } finally {
      setIsSaving(false);
    }
  };

  // Nothing selected and not new
  if (!offer && !isNew) {
    return (
      <div style={emptyPanelStyle}>
        Select an offer or create a new one
      </div>
    );
  }

  const panelTitle = isNew ? "New Offer" : form.coupon_code;
  const statusColor = STATUS_COLORS[form.status] ?? "var(--text-secondary)";

  const hierarchyValues6: {
    h1_org_scope: string;
    h2_org_scope: string;
    h3_org_scope: string;
    h4_loyalty_type: string;
    h5_discount_type: string;
    h6_item_structure: string;
  } = {
    h1_org_scope: form.h1_org_scope,
    h2_org_scope: form.h2_org_scope,
    h3_org_scope: form.h3_org_scope,
    h4_loyalty_type: form.h4_loyalty_type,
    h5_discount_type: form.h5_discount_type,
    h6_item_structure: form.h6_item_structure,
  };

  return (
    <div style={{ ...panelStyle, position: "relative" }}>
      {isSaving && (
        <div style={savingOverlayStyle}>Saving...</div>
      )}

      {/* Header */}
      <div style={headerStyle}>
        <span style={titleStyle}>{panelTitle}</span>
        {!isNew && (
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              color: statusColor,
              marginLeft: 4,
            }}
          >
            {form.status}
          </span>
        )}
      </div>

      {/* Scroll area */}
      <div style={scrollAreaStyle}>
        {/* Basic fields */}
        <div style={sectionLabelFirstStyle}>Offer Details</div>
        <div style={fieldRowStyle}>
          <div style={fieldStyle}>
            <label style={fieldLabelStyle}>Coupon Code</label>
            <input
              style={monoInputStyle}
              value={form.coupon_code}
              onChange={(e) => handleChange("coupon_code", e.target.value)}
              placeholder="e.g. SAVE10"
            />
          </div>
          <div style={fieldStyle}>
            <label style={fieldLabelStyle}>Dollar Amount</label>
            <input
              style={inputStyle}
              type="number"
              step="0.01"
              min="0"
              value={form.dollar_amount}
              onChange={(e) => handleChange("dollar_amount", e.target.value)}
              placeholder="e.g. 5.00"
            />
          </div>
          <div style={fieldStyle}>
            <label style={fieldLabelStyle}>Status</label>
            <span
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: statusColor,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                padding: "6px 0",
              }}
            >
              {form.status}
            </span>
          </div>
        </div>

        <div style={{ ...fieldStyle, marginTop: 10, marginBottom: 4 }}>
          <label style={fieldLabelStyle}>Description</label>
          <textarea
            style={textareaStyle}
            value={form.description}
            onChange={(e) => handleChange("description", e.target.value)}
            placeholder="Brief description of the offer"
          />
        </div>

        <div style={{ ...fieldRowStyle, marginTop: 10 }}>
          <div style={fieldStyle}>
            <label style={fieldLabelStyle}>Start Date</label>
            <input
              style={inputStyle}
              type="date"
              value={form.start_date}
              onChange={(e) => handleChange("start_date", e.target.value)}
            />
          </div>
          <div style={fieldStyle}>
            <label style={fieldLabelStyle}>End Date</label>
            <input
              style={inputStyle}
              type="date"
              value={form.end_date}
              onChange={(e) => handleChange("end_date", e.target.value)}
            />
          </div>
          <div />
        </div>

        {/* Hierarchy */}
        <div style={sectionLabelStyle}>Hierarchy Classification</div>
        <HierarchyFields
          values={hierarchyValues6}
          hierarchyValues={hierarchyValues}
          onChange={handleHierarchyChange}
          disabled={isLoading}
        />

        {/* Menu Items */}
        <div style={sectionLabelStyle}>Menu Items</div>
        <MenuItemPicker
          selectedIds={form.menu_item_ids}
          menuItems={menuItems}
          onChange={handleMenuItemChange}
          disabled={isLoading}
        />

        {/* Bottom padding */}
        <div style={{ height: 20 }} />
      </div>

      {/* Action bar */}
      <div style={actionBarStyle}>
        <button
          style={saveBtnStyle(!isDirty || isSaving)}
          disabled={!isDirty || isSaving}
          onClick={handleSave}
          type="button"
        >
          {isSaving ? "Saving..." : "Save"}
        </button>
        <button
          style={resetBtnStyle}
          onClick={handleReset}
          type="button"
        >
          Reset
        </button>

        {/* Status transition */}
        {!isNew && form.status === "draft" && (
          <button
            style={transitionBtnStyle("var(--status-active)")}
            onClick={() => handleStatusTransition("active")}
            type="button"
          >
            Activate
          </button>
        )}
        {!isNew && form.status === "active" && (
          <button
            style={transitionBtnStyle("var(--text-secondary)")}
            onClick={() => handleStatusTransition("expired")}
            type="button"
          >
            Mark Expired
          </button>
        )}
      </div>
    </div>
  );
};

export default OfferEditor;
