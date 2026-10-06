import { request } from "./client";

export const getRooms = () => request("/rooms");

// date: "YYYY-MM-DD"
export const getRoomReservations = (roomId, date) =>
  request(`/rooms/${roomId}/reservations`, { query: { date } });

export const getStudyReservations = (studyId) => request(`/studies/${studyId}/reservations`);

// { user_id, room_id, start_at, end_at }
export const createReservation = (studyId, body) =>
  request(`/studies/${studyId}/reservations`, { method: "POST", body });

export const cancelReservation = (id, userId) =>
  request(`/reservations/${id}`, { method: "DELETE", query: { user_id: userId } });
