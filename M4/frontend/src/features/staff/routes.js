import StaffList from './StaffList.svelte';

export const routes = [
	{ path: '/app/staff', title: 'Staff', roles: ['admin'], component: StaffList }
];
