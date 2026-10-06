import { request } from "./client";

export const getStudies = (status) => request("/studies", { query: { status } });

export const getStudy = (id) => request(`/studies/${id}`);

// { owner_id, title, description, capacity }
export const createStudy = (body) => request("/studies", { method: "POST", body });

export const updateCapacity = (id, userId, capacity) =>
  request(`/studies/${id}/capacity`, { method: "PATCH", body: { user_id: userId, capacity } });

export const transferOwner = (id, userId, newOwnerId) =>
  request(`/studies/${id}/transfer-owner`, {
    method: "POST",
    body: { user_id: userId, new_owner_id: newOwnerId },
  });
