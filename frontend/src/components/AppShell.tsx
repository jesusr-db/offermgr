import React from "react";
import type { Persona } from "../types";

interface AppShellProps {
  children: React.ReactNode;
  persona: string;
  personas: Persona[];
  onPersonaChange: (id: string) => void;
}

const NAV_HEIGHT = 52;

const navStyle: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  right: 0,
  height: NAV_HEIGHT,
  background: "var(--dpz-surface)",
  borderBottom: "1px solid var(--border-default)",
  display: "flex",
  alignItems: "center",
  padding: "0 16px",
  gap: 12,
  zIndex: 100,
};

const logoStyle: React.CSSProperties = {
  width: 32,
  height: 32,
  background: "var(--dpz-red)",
  borderRadius: 4,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontWeight: 700,
  fontSize: 18,
  color: "#fff",
  flexShrink: 0,
  fontFamily: "var(--font-family)",
  letterSpacing: "-0.5px",
};

const titleStyle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: 15,
  color: "var(--text-primary)",
  letterSpacing: "-0.2px",
};

const spacerStyle: React.CSSProperties = { flex: 1 };

const personaLabelStyle: React.CSSProperties = {
  fontSize: 12,
  color: "var(--text-secondary)",
  marginRight: 4,
};

const selectStyle: React.CSSProperties = {
  background: "var(--dpz-surface-elevated)",
  color: "var(--text-primary)",
  border: "1px solid var(--border-default)",
  borderRadius: 4,
  padding: "4px 8px",
  fontSize: 13,
  cursor: "pointer",
  outline: "none",
  fontFamily: "var(--font-family)",
};

const mainStyle: React.CSSProperties = {
  marginTop: NAV_HEIGHT,
  height: `calc(100vh - ${NAV_HEIGHT}px)`,
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
};

const AppShell: React.FC<AppShellProps> = ({
  children,
  persona,
  personas,
  onPersonaChange,
}) => {
  return (
    <>
      <nav style={navStyle}>
        <div style={logoStyle}>D</div>
        <span style={titleStyle}>Offer Management</span>
        <div style={spacerStyle} />
        <span style={personaLabelStyle}>View as:</span>
        <select
          style={selectStyle}
          value={persona}
          onChange={(e) => onPersonaChange(e.target.value)}
        >
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </nav>
      <main style={mainStyle}>{children}</main>
    </>
  );
};

export default AppShell;
