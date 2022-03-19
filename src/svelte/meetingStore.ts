import { Writable, writable } from "svelte/store";

export const meeting: Writable<MeetingInfo> = writable();

type MeetingInfo = {
    id?: string;
    password?: string;
    host?: boolean;
    temporary: boolean;
};