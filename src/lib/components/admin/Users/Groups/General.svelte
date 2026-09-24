<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { getGroups } from '$lib/apis/groups';
	import Textarea from '$lib/components/common/Textarea.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	export let name = '';
	export let color = '';
	export let description = '';
	export let data: Record<string, any> = {};

	export let edit = false;
	export let onDelete: Function = () => {};

	type GroupOption = { id: string; name: string };

	let groups: GroupOption[] = [];
	let groupsLoaded = false;

	$: shareGroupIds = (
		Array.isArray(data?.config?.share_group_ids) ? data.config.share_group_ids : []
	) as string[];
	// Ids of deleted groups (or all ids, if the list failed to load) show as "Unknown" so they can be removed
	$: selectedShareGroups = shareGroupIds.map((id) => ({
		id,
		name: groups.find((group) => group.id === id)?.name ?? null
	}));
	$: availableShareGroups = groups.filter((group) => !shareGroupIds.includes(group.id));

	const shareChangeHandler = (value: string) => {
		let shareValue;
		if (value === 'false') {
			shareValue = false;
		} else if (value === 'true') {
			shareValue = true;
		} else {
			shareValue = value;
		}

		// share_group_ids is kept when switching modes so the selection survives toggling; it only applies to 'groups'
		data.config = {
			...(data?.config ?? {}),
			share: shareValue,
			...(shareValue === 'groups' ? { share_group_ids: shareGroupIds } : {})
		};
	};

	const addShareGroup = (id: string) => {
		if (!id || shareGroupIds.includes(id)) {
			return;
		}
		data.config = { ...(data?.config ?? {}), share_group_ids: [...shareGroupIds, id] };
	};

	const removeShareGroup = (id: string) => {
		data.config = {
			...(data?.config ?? {}),
			share_group_ids: shareGroupIds.filter((groupId) => groupId !== id)
		};
	};

	onMount(async () => {
		try {
			groups = (await getGroups(localStorage.token)) ?? [];
		} catch (error) {
			console.error(error);
			groups = [];
		}
		groupsLoaded = true;
	});
</script>

<div class="flex gap-2">
	<div class="flex flex-col w-full">
		<div class=" mb-0.5 text-xs text-gray-500">{$i18n.t('Name')}</div>

		<div class="flex-1">
			<input
				class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
				type="text"
				bind:value={name}
				placeholder={$i18n.t('Group Name')}
				autocomplete="off"
				required
			/>
		</div>
	</div>
</div>

<!-- <div class="flex flex-col w-full mt-2">
	<div class=" mb-1 text-xs text-gray-500">{$i18n.t('Color')}</div>

	<div class="flex-1">
		<Tooltip content={$i18n.t('Hex Color - Leave empty for default color')} placement="top-start">
			<div class="flex gap-0.5">
				<div class="text-gray-500">#</div>

				<input
					class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
					type="text"
					bind:value={color}
					placeholder={$i18n.t('Hex Color')}
					autocomplete="off"
				/>
			</div>
		</Tooltip>
	</div>
</div> -->

<div class="flex flex-col w-full mt-2">
	<div class=" mb-1 text-xs text-gray-500">{$i18n.t('Description')}</div>

	<div class="flex-1">
		<Textarea
			className="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden resize-none"
			rows={4}
			bind:value={description}
			placeholder={$i18n.t('Group Description')}
		/>
	</div>
</div>

<hr class="border-gray-50 dark:border-gray-850/30 my-1" />

<div class="flex flex-col w-full mt-2">
	<div class=" mb-1 text-xs text-gray-500">{$i18n.t('Setting')}</div>

	<div>
		<div class=" flex w-full justify-between">
			<div class=" self-center text-xs">
				{$i18n.t('Who can share to this group')}
			</div>

			<div class="flex items-center gap-2 p-1">
				<select
					class="text-sm bg-transparent outline-hidden rounded-lg pl-2 pr-5"
					value={data?.config?.share ?? 'members'}
					aria-label={$i18n.t('Who can share to this group')}
					on:change={(e) => shareChangeHandler(e.currentTarget.value)}
				>
					<option value={false}>{$i18n.t('No one')}</option>
					<option value="members">{$i18n.t('Members')}</option>
					<option value="groups">{$i18n.t('Specific groups')}</option>
					<option value={true}>{$i18n.t('Anyone')}</option>
				</select>
			</div>
		</div>

		{#if data?.config?.share === 'groups'}
			<div class="flex flex-col gap-1.5 mt-1">
				<div class="flex flex-wrap items-center gap-1">
					{#if !groupsLoaded}
						<div class="text-xs text-gray-400 dark:text-gray-500">{$i18n.t('Loading...')}</div>
					{:else}
						{#each selectedShareGroups as group (group.id)}
							<div
								class="flex items-center gap-1 text-xs pl-2 pr-1 py-0.5 rounded-lg bg-gray-100 dark:bg-gray-850 {group.name ===
								null
									? 'text-gray-400 dark:text-gray-500'
									: ''}"
								title={group.name === null ? group.id : undefined}
							>
								<span class="line-clamp-1">{group.name ?? $i18n.t('Unknown')}</span>
								<button
									class="rounded-full p-0.5 text-gray-500 hover:text-gray-900 hover:bg-gray-200 dark:hover:text-white dark:hover:bg-gray-800 transition"
									type="button"
									aria-label={`${$i18n.t('Remove')} ${group.name ?? $i18n.t('Unknown')}`}
									on:click={() => removeShareGroup(group.id)}
								>
									<XMark className="size-3" />
								</button>
							</div>
						{:else}
							<div class="text-xs text-gray-400 dark:text-gray-500">
								{$i18n.t('No groups selected')}
							</div>
						{/each}
					{/if}
				</div>

				<select
					class="w-full text-sm bg-transparent outline-hidden rounded-lg pr-5 text-gray-500 dark:text-gray-400"
					value=""
					aria-label={$i18n.t('Select a group')}
					on:change={(e) => {
						addShareGroup(e.currentTarget.value);
						e.currentTarget.value = '';
					}}
				>
					<option value="" disabled>{$i18n.t('Select a group')}</option>
					{#each availableShareGroups as group (group.id)}
						<option value={group.id}>{group.name}</option>
					{/each}
				</select>

				<div class="text-xs text-gray-500">
					{$i18n.t(
						'Only members of the selected groups can share to this group. Admins can always share.'
					)}
				</div>
			</div>
		{/if}
	</div>
</div>

{#if edit}
	<div class="flex flex-col w-full mt-2">
		<div class=" mb-0.5 text-xs text-gray-500">{$i18n.t('Actions')}</div>

		<div class="flex-1">
			<button
				class="text-xs bg-transparent hover:underline cursor-pointer"
				type="button"
				on:click={() => onDelete()}
			>
				{$i18n.t('Delete')}
			</button>
		</div>
	</div>
{/if}
