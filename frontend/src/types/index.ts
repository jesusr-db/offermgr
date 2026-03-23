export interface MenuItem {
  item_id: string;
  name: string;
  category: string;
  base_price: number;
}

export interface Offer {
  offer_id: string;
  coupon_code: string;
  description: string;
  status: "draft" | "active" | "expired";
  start_date: string;       // YYYY-MM-DD
  end_date: string;         // YYYY-MM-DD
  dollar_amount: number | null;
  h1_org_scope: string;
  h2_org_scope: string;
  h3_org_scope: string;
  h4_loyalty_type: string;
  h5_discount_type: string;
  h6_item_structure: string;
  persona_scope: string;
  persona_scope_id: string | null;
  created_at: string;
  updated_at: string;
  menu_items?: MenuItem[];  // present in single-offer detail response
}

export interface Persona {
  id: string;
  label: string;
  scope: string;
  scope_id: string | null;
}

export interface HierarchyValues {
  h1_org_scope: string[];
  h2_org_scope: string[];
  h3_org_scope: string[];
  h4_loyalty_type: string[];
  h5_discount_type: string[];
  h6_item_structure: string[];
}

export interface OfferFilters {
  search: string;
  status: string;
  h5_discount_type: string;
  h1_org_scope: string;
}

export type OfferStatus = "draft" | "active" | "expired";
