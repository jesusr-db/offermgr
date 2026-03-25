import React, { useState, useEffect } from "react";
import type { Persona, HierarchyValues, MenuItem, Offer } from "./types";
import { useOffers } from "./hooks/useOffers";
import AppShell from "./components/AppShell";
import FilterBar from "./components/FilterBar";
import OfferList from "./components/OfferList";
import OfferEditor from "./components/OfferEditor";

const EMPTY_HIERARCHY: HierarchyValues = {
  h1_org_scope: [],
  h2_org_scope: [],
  h3_org_scope: [],
  h4_loyalty_type: [],
  h5_discount_type: [],
  h6_item_structure: [],
};

const FALLBACK_PERSONA: Persona = {
  id: "global",
  label: "Global (all markets)",
  scope: "global",
  scope_id: null,
};

const App: React.FC = () => {
  const [personas, setPersonas] = useState<Persona[]>([FALLBACK_PERSONA]);
  const [hierarchyValues, setHierarchyValues] =
    useState<HierarchyValues>(EMPTY_HIERARCHY);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [isNew, setIsNew] = useState(false);
  const [dirtyOfferIds, setDirtyOfferIds] = useState<Set<string>>(new Set());

  const {
    offers,
    selectedOffer,
    filters,
    isLoadingList,
    isLoadingDetail,
    persona,
    setFilters,
    setPersona,
    selectOffer,
    createOffer,
    updateOffer,
  } = useOffers(FALLBACK_PERSONA.id);

  // Fetch personas
  useEffect(() => {
    fetch("/api/personas")
      .then((r) => r.ok ? r.json() as Promise<Persona[]> : Promise.resolve([]))
      .then((data) => {
        if (data.length > 0) setPersonas(data);
      })
      .catch(() => {/* keep fallback */});
  }, []);

  // Fetch hierarchy values
  useEffect(() => {
    fetch("/api/hierarchy-values")
      .then((r) => r.ok ? r.json() as Promise<HierarchyValues> : Promise.resolve(EMPTY_HIERARCHY))
      .then(setHierarchyValues)
      .catch(() => {/* keep empty */});
  }, []);

  // Fetch menu items (no persona header needed)
  useEffect(() => {
    fetch("/api/menu-items")
      .then((r) => r.ok ? r.json() as Promise<MenuItem[]> : Promise.resolve([]))
      .then(setMenuItems)
      .catch(() => {/* keep empty */});
  }, []);

  // When persona changes in the dropdown, reset filters/selection and update hook
  const handlePersonaChange = (id: string) => {
    setPersona(id);
    setFilters({ search: "", status: "", h4_loyalty_type: "", h5_discount_type: "", h6_item_structure: "", h1_org_scope: "" });
    selectOffer(null);
    setIsNew(false);
  };

  // New offer handler
  const handleNewOffer = () => {
    selectOffer(null);
    setIsNew(true);
  };

  // Select existing offer
  const handleSelectOffer = (id: string) => {
    setIsNew(false);
    selectOffer(id);
  };

  // Mark a dirty offer
  const handleMarkDirty = () => {
    if (selectedOffer) {
      setDirtyOfferIds((prev) => new Set([...prev, selectedOffer.offer_id]));
    }
    // For new offers there's no ID yet — dirtyness is implicit from isNew
  };

  // Save handler
  const handleSave = async (
    data: Partial<Offer> & { menu_item_ids?: string[] }
  ) => {
    if (isNew) {
      const code = data.coupon_code || `_${Date.now().toString().slice(-4)}`;
      await createOffer({
        coupon_code: code,
        description: data.description ?? "",
        start_date: data.start_date ?? "",
        end_date: data.end_date ?? "",
        ...data,
      });
      setIsNew(false);
    } else if (selectedOffer) {
      await updateOffer(selectedOffer.offer_id, data);
      setDirtyOfferIds((prev) => {
        const next = new Set(prev);
        next.delete(selectedOffer.offer_id);
        return next;
      });
    }
  };

  // Reset handler
  const handleReset = () => {
    if (selectedOffer) {
      setDirtyOfferIds((prev) => {
        const next = new Set(prev);
        next.delete(selectedOffer.offer_id);
        return next;
      });
    }
    if (isNew) {
      setIsNew(false);
    }
  };

  return (
    <AppShell
      persona={persona}
      personas={personas}
      onPersonaChange={handlePersonaChange}
    >
      <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        <FilterBar
          filters={filters}
          hierarchyValues={hierarchyValues}
          offerCount={offers.length}
          onFilterChange={setFilters}
          onNewOffer={handleNewOffer}
        />
        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          <OfferList
            offers={offers}
            selectedOfferId={
              isNew ? null : (selectedOffer?.offer_id ?? null)
            }
            dirtyOfferIds={dirtyOfferIds}
            isLoading={isLoadingList}
            onSelect={handleSelectOffer}
          />
          <OfferEditor
            offer={isNew ? null : selectedOffer}
            isNew={isNew}
            menuItems={menuItems}
            hierarchyValues={hierarchyValues}
            isLoading={isLoadingDetail}
            onSave={handleSave}
            onReset={handleReset}
            onMarkDirty={handleMarkDirty}
          />
        </div>
      </div>
    </AppShell>
  );
};

export default App;
