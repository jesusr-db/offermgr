import React from "react";
import type { Offer } from "../types";
import OfferListItem from "./OfferListItem";

interface OfferListProps {
  offers: Offer[];
  selectedOfferId: string | null;
  dirtyOfferIds: Set<string>;
  isLoading: boolean;
  onSelect: (id: string) => void;
}

const listContainerStyle: React.CSSProperties = {
  width: 280,
  flexShrink: 0,
  borderRight: "1px solid var(--border-default)",
  overflowY: "auto",
  height: "100%",
  background: "var(--dpz-dark)",
};

const stateStyle: React.CSSProperties = {
  padding: 24,
  fontSize: 13,
  color: "var(--text-secondary)",
  textAlign: "center",
};

const OfferList: React.FC<OfferListProps> = ({
  offers,
  selectedOfferId,
  dirtyOfferIds,
  isLoading,
  onSelect,
}) => {
  if (isLoading) {
    return (
      <div style={listContainerStyle}>
        <div style={stateStyle}>Loading offers...</div>
      </div>
    );
  }

  if (offers.length === 0) {
    return (
      <div style={listContainerStyle}>
        <div style={stateStyle}>No offers found</div>
      </div>
    );
  }

  return (
    <div style={listContainerStyle}>
      {offers.map((offer) => (
        <OfferListItem
          key={offer.offer_id}
          offer={offer}
          isSelected={offer.offer_id === selectedOfferId}
          isDirty={dirtyOfferIds.has(offer.offer_id)}
          onClick={() => onSelect(offer.offer_id)}
        />
      ))}
    </div>
  );
};

export default OfferList;
