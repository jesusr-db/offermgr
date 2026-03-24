import { useState, useEffect, useCallback } from "react";
import type { Offer, OfferFilters } from "../types";

const DEFAULT_FILTERS: OfferFilters = {
  search: "",
  status: "",
  h4_loyalty_type: "",
  h5_discount_type: "",
  h6_item_structure: "",
  h1_org_scope: "",
};

interface CreateOfferPayload {
  coupon_code: string;
  description: string;
  start_date: string;
  end_date: string;
  menu_item_ids?: string[];
  [key: string]: unknown;
}

interface UpdateOfferPayload {
  menu_item_ids?: string[];
  [key: string]: unknown;
}

export interface UseOffersReturn {
  // Data
  offers: Offer[];
  selectedOffer: Offer | null;

  // State
  filters: OfferFilters;
  isLoadingList: boolean;
  isLoadingDetail: boolean;
  persona: string;

  // Actions
  setFilters: (filters: Partial<OfferFilters>) => void;
  setPersona: (personaId: string) => void;
  selectOffer: (offerId: string | null) => void;
  createOffer: (data: CreateOfferPayload) => Promise<string>;
  updateOffer: (offerId: string, data: UpdateOfferPayload) => Promise<void>;
  refreshList: () => void;
}

function buildQueryString(filters: OfferFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== "") {
      params.set(key, value);
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function useOffers(initialPersona = ""): UseOffersReturn {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [selectedOffer, setSelectedOffer] = useState<Offer | null>(null);
  const [filters, setFiltersState] = useState<OfferFilters>(DEFAULT_FILTERS);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [persona, setPersonaState] = useState<string>(initialPersona);
  const [listRevision, setListRevision] = useState(0);

  const makeHeaders = useCallback(
    (): HeadersInit => ({
      "Content-Type": "application/json",
      ...(persona ? { "X-Persona": persona } : {}),
    }),
    [persona]
  );

  // Fetch list whenever filters, persona, or listRevision change
  useEffect(() => {
    let cancelled = false;
    const qs = buildQueryString(filters);

    setIsLoadingList(true);
    fetch(`/api/offers${qs}`, { headers: makeHeaders() })
      .then((res) => {
        if (!res.ok) throw new Error(`List fetch failed: ${res.status}`);
        return res.json() as Promise<Offer[]>;
      })
      .then((data) => {
        if (!cancelled) {
          setOffers(data);
          setIsLoadingList(false);
        }
      })
      .catch(() => {
        if (!cancelled) setIsLoadingList(false);
      });

    return () => {
      cancelled = true;
    };
  }, [filters, persona, listRevision, makeHeaders]);

  const setFilters = useCallback((partial: Partial<OfferFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...partial }));
  }, []);

  const setPersona = useCallback((personaId: string) => {
    setPersonaState(personaId);
  }, []);

  const refreshList = useCallback(() => {
    setListRevision((n) => n + 1);
  }, []);

  const selectOffer = useCallback(
    (offerId: string | null) => {
      if (offerId === null) {
        setSelectedOffer(null);
        return;
      }
      setIsLoadingDetail(true);
      fetch(`/api/offers/${offerId}`, { headers: makeHeaders() })
        .then((res) => {
          if (!res.ok) throw new Error(`Detail fetch failed: ${res.status}`);
          return res.json() as Promise<Offer>;
        })
        .then((data) => {
          setSelectedOffer(data);
          setIsLoadingDetail(false);
        })
        .catch(() => {
          setIsLoadingDetail(false);
        });
    },
    [makeHeaders]
  );

  const createOffer = useCallback(
    async (data: CreateOfferPayload): Promise<string> => {
      const res = await fetch("/api/offers", {
        method: "POST",
        headers: makeHeaders(),
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Create failed (${res.status}): ${text}`);
      }
      const created = (await res.json()) as Offer;
      refreshList();
      selectOffer(created.offer_id);
      return created.offer_id;
    },
    [makeHeaders, refreshList, selectOffer]
  );

  const updateOffer = useCallback(
    async (offerId: string, data: UpdateOfferPayload): Promise<void> => {
      const res = await fetch(`/api/offers/${offerId}`, {
        method: "PUT",
        headers: makeHeaders(),
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Update failed (${res.status}): ${text}`);
      }
      // Refresh the list so the updated row (e.g. new updated_at) appears.
      // Do NOT call selectOffer here — re-fetching would trigger OfferEditor's
      // useEffect and reset the form back to server data, making edits appear
      // lost even when the save succeeded.
      refreshList();
    },
    [makeHeaders, refreshList]
  );

  return {
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
    refreshList,
  };
}
