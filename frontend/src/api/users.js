import { request } from "./client";

export const getUsers = () => request("/users");

export const createUser = (nickname) =>
  request("/users", { method: "POST", body: { nickname } });

export const getMyApplications = (userId) => request(`/users/${userId}/applications`);

export const seed = () => request("/seed", { method: "POST" });
