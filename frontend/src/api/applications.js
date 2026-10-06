import { request } from "./client";

export const applyStudy = (studyId, userId, message) =>
  request(`/studies/${studyId}/applications`, {
    method: "POST",
    body: { user_id: userId, message },
  });

// 방장만 조회 가능
export const getApplications = (studyId, userId, status) =>
  request(`/studies/${studyId}/applications`, { query: { user_id: userId, status } });

export const cancelApplication = (id, userId) =>
  request(`/applications/${id}`, { method: "DELETE", query: { user_id: userId } });

export const approveApplication = (id, userId) =>
  request(`/applications/${id}/approve`, { method: "POST", body: { user_id: userId } });

export const rejectApplication = (id, userId) =>
  request(`/applications/${id}/reject`, { method: "POST", body: { user_id: userId } });
