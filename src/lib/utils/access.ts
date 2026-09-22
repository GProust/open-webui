export type AccessGrant = {
	id?: string;
	principal_type: 'user' | 'group' | 'anyone';
	principal_id: string;
	permission: 'read' | 'write';
};

const grantKey = (grant: AccessGrant): string =>
	`${grant.principal_type}:${grant.principal_id}:${grant.permission}`;

export const toAccessGrants = (grants: any): AccessGrant[] =>
	Array.isArray(grants)
		? grants.filter((grant) => grant?.principal_type && grant?.principal_id && grant?.permission)
		: [];

/**
 * Reconcile a submitted access-grant list against what the server stored.
 *
 * The server drops grants the caller has no permission to assign, so the list
 * it saved can be smaller than the one that was sent. Without this the UI keeps
 * rendering the grants it submitted and shows access that was never persisted.
 *
 * `grants` is what the server actually stored, ready to bind back into the
 * editor; `rejected` is what it refused. When the response carries no grant
 * list we keep the submitted one rather than blanking the editor.
 */
export const reconcileAccessGrants = (
	submitted: any,
	response: any
): { grants: AccessGrant[]; rejected: AccessGrant[] } => {
	const submittedGrants = toAccessGrants(submitted);

	if (!Array.isArray(response?.access_grants)) {
		return { grants: submittedGrants, rejected: [] };
	}

	const savedGrants = toAccessGrants(response.access_grants);
	const savedKeys = new Set(savedGrants.map(grantKey));

	return {
		grants: savedGrants,
		rejected: submittedGrants.filter((grant) => !savedKeys.has(grantKey(grant)))
	};
};
