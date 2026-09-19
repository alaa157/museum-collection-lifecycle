import { getAccessToken } from "@/lib/auth";
import { apiRequest } from "@/lib/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";

export type CollectionItem = {
  id: string;
  accession_number: string;
  object_number: string;
  title: string;
  status: string;
  current_location_id: number | null;
  object_type_id: number | null;
  culture_id: number | null;
  value: number | null;
  insurance_value: number | null;
  version: number;
  created_at: string;
};

export type CollectionPage = {
  items: CollectionItem[];
  total: number;
  offset: number;
  limit: number;
};

export type MovementRequest = {
  id: number;
  collection_item_id: string;
  from_location_id: number | null;
  to_location_id: number;
  requested_by: number;
  approved_by: number | null;
  reason: string;
  status: string;
  created_at: string;
};

export type ConditionReport = {
  id: number;
  collection_item_id: string;
  condition_score: number;
  observed_damage: string | null;
  environmental_concerns: string | null;
  recommendations: string | null;
  inspector_id: number;
  report_date: string;
};

export type Treatment = {
  id: number;
  collection_item_id: string;
  treatment_type: string;
  conservator_id: number;
  start_date: string | null;
  end_date: string | null;
  status: string;
};

export type Loan = {
  id: number;
  direction: string;
  party_id: number;
  start_date: string;
  due_date: string;
  insurance_value: number | null;
  status: string;
};

export const domainApi = {
  collection: {
    list(params?: URLSearchParams) {
      const query = params ? `?${params.toString()}` : "";
      return apiRequest<CollectionPage>(`/collection/items${query}`);
    },

    get(id: string) {
      return apiRequest<CollectionItem>(`/collection/items/${id}`);
    },

    create(payload: unknown) {
      return apiRequest<CollectionItem>("/collection/items", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    locations() {
      return apiRequest<Array<{
        id: number;
        name: string;
        location_type: string;
        parent_id: number | null;
      }>>("/collection/locations");
    },

    requestMovement(itemId: string, payload: unknown) {
      return apiRequest<MovementRequest>(
        `/collection/items/${itemId}/movements`,
        {
          method: "POST",
          body: JSON.stringify(payload)
        }
      );
    },

    movements() {
      return apiRequest<MovementRequest[]>("/collection/movements");
    },

    movementStatus(id: number, status: string) {
      return apiRequest<MovementRequest>(`/collection/movements/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status })
      });
    },

    provenance(id: string) {
      return apiRequest<any[]>(`/collection/items/${id}/provenance`);
    }
  },

  conservation: {
    conditionReports(itemId: string) {
      return apiRequest<ConditionReport[]>(
        `/conservation/condition-reports/${itemId}`
      );
    },

    treatments(itemId: string) {
      return apiRequest<Treatment[]>(
        `/conservation/treatments/${itemId}`
      );
    },

    createConditionReport(payload: unknown) {
      return apiRequest<ConditionReport>("/conservation/condition-reports", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    createTreatment(payload: unknown) {
      return apiRequest<Treatment>("/conservation/treatments", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    updateTreatmentStatus(id: number, status: string) {
      return apiRequest<Treatment>(
        `/conservation/treatments/${id}/status`,
        {
          method: "PATCH",
          body: JSON.stringify({ status })
        }
      );
    }
  },

  loans: {
    list() {
      return apiRequest<Loan[]>("/loans");
    },

    create(payload: unknown) {
      return apiRequest<Loan>("/loans", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    updateStatus(id: number, status: string) {
      return apiRequest<Loan>(`/loans/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status })
      });
    },

    exhibitions() {
      return apiRequest<any[]>("/loans/exhibitions/list");
    },

    createExhibition(payload: unknown) {
      return apiRequest<any>("/loans/exhibitions", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    updateExhibitionStatus(id: number, status: string) {
      return apiRequest<any>(`/loans/exhibitions/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status })
      });
    }
  },

  notifications: {
    list() {
      return apiRequest<any[]>("/notifications");
    },

    markRead(id: number) {
      return apiRequest<any>(`/notifications/${id}/read`, {
        method: "PATCH"
      });
    },

    markAllRead() {
      return apiRequest<{ updated: number }>("/notifications/read-all", {
        method: "POST"
      });
    }
  },

  audit: {
    list(params?: URLSearchParams) {
      const query = params ? `?${params.toString()}` : "";
      return apiRequest<any[]>(`/audit${query}`);
    }
  }
};
