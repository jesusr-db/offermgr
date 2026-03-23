import React from "react";
import type { Offer } from "../types";

interface OfferListItemProps {
  offer: Offer;
  isSelected: boolean;
  isDirty: boolean;
  onClick: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  active: "var(--status-active)",
  draft: "var(--status-draft)",
  expired: "var(--status-expired)",
};

const OfferListItem: React.FC<OfferListItemProps> = ({
  offer,
  isSelected,
  isDirty,
  onClick,
}) => {
  const statusColor = STATUS_COLORS[offer.status] ?? "var(--text-secondary)";

  const rowStyle: React.CSSProperties = {
    padding: "10px 12px",
    cursor: "pointer",
    borderLeft: isSelected
      ? "3px solid var(--dpz-blue)"
      : "3px solid transparent",
    background: isSelected
      ? "var(--dpz-surface-elevated)"
      : "transparent",
    borderBottom: "1px solid var(--border-default)",
    transition: "background 0.1s",
  };

  const headerRowStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: 6,
    marginBottom: 3,
  };

  const codeStyle: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontWeight: 700,
    fontSize: 13,
    color: "var(--text-primary)",
    letterSpacing: "0.3px",
  };

  const dirtyDotStyle: React.CSSProperties = {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: "var(--dpz-blue)",
    flexShrink: 0,
  };

  const badgeStyle: React.CSSProperties = {
    marginLeft: "auto",
    fontSize: 10,
    fontWeight: 700,
    textTransform: "uppercase" as const,
    color: statusColor,
    letterSpacing: "0.5px",
  };

  const descStyle: React.CSSProperties = {
    fontSize: 12,
    color: "var(--text-secondary)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    marginBottom: 4,
  };

  const metaStyle: React.CSSProperties = {
    fontSize: 11,
    color: "var(--text-muted)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  };

  return (
    <div style={rowStyle} onClick={onClick} role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onClick(); }}
    >
      <div style={headerRowStyle}>
        <span style={codeStyle}>{offer.coupon_code}</span>
        {isDirty && <span style={dirtyDotStyle} title="Unsaved changes" />}
        <span style={badgeStyle}>{offer.status}</span>
      </div>
      <div style={descStyle}>{offer.description || "\u00a0"}</div>
      <div style={metaStyle}>
        {[offer.h5_discount_type, offer.h6_item_structure]
          .filter(Boolean)
          .join(" · ") || "\u00a0"}
      </div>
    </div>
  );
};

export default OfferListItem;
