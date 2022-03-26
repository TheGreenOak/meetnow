import { Writable, writable } from "svelte/store";

export const meeting: Writable<MeetingInfo> = writable();
export const notifications: Writable<NotificationInfo> = writable();

type MeetingInfo = {
    id?: string;
    password?: string;
    host?: boolean;

    connected?: boolean;
    disconnected?: boolean;
    ready?: boolean;
    
    temporary: boolean;
};

export type NotificationInfo = {
    data: string;
    type: "success" | "info" | "error";
};