import { createContext } from 'svelte';

/** @type {ReturnType<typeof createContext<() => ReturnType<typeof import('./form.js').createForm>>>} */
const context = createContext();
export const getFormContext = context[0];
export const setFormContext = context[1];
