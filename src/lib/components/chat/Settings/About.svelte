<script lang="ts">
	import { getOllamaVersion } from '$lib/apis/ollama';
	import { WEBUI_BUILD_HASH, WEBUI_VERSION } from '$lib/constants';
	import { WEBUI_NAME, config } from '$lib/stores';
	import { onMount, getContext } from 'svelte';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');

	let ollamaVersion = '';

	onMount(async () => {
		ollamaVersion = await getOllamaVersion(localStorage.token).catch((error) => {
			return '';
		});
	});
</script>

<div id="tab-about" class="flex flex-col h-full justify-between space-y-3 text-sm mb-6">
	<div class=" space-y-3 overflow-y-scroll max-h-[28rem] md:max-h-full">
		<div>
			<div class=" mb-2.5 text-sm font-medium flex space-x-2 items-center">
				<div>
					{$WEBUI_NAME} CHAT
					{$i18n.t('Version')}
					(<a href="https://github.com/ovinc-cn/OpenWebUI" target="_blank" style="color: unset"
						>基于 OVINC-CN、{$i18n.t('Second revision by Open WebUI')}</a
					>)
				</div>
			</div>
		<div class="flex w-full">
			<div class="flex-1 text-xs text-gray-700 dark:text-gray-200">
				v{WEBUI_VERSION}
			</div>
		</div>
		</div>

		<hr class=" border-gray-100 dark:border-gray-850" />
		
		<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
			本项目离不开 Open WebUI 开源项目的支持，感谢 Open WebUI 提供了完美的项目支撑！
		</div>

		<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
			同时，本项目还要特别感谢方块 OVINC-CN 的二开版本，为项目进行了完美的生态适配！
		</div>

		<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
			Chenyme 对所有相关开发人员表示感谢！
		</div>

		<hr class=" border-gray-100 dark:border-gray-850" />

		<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
			Emoji graphics provided by
			<a href="https://github.com/jdecked/twemoji" target="_blank">Twemoji</a>, licensed under
			<a href="https://creativecommons.org/licenses/by/4.0/" target="_blank">CC-BY 4.0</a>.
		</div>

		<div>
			<pre
				class="text-xs text-gray-400 dark:text-gray-500">Copyright (c) {new Date().getFullYear()} <a
					href="https://OpenWebUI.com"
					target="_blank"
					class="underline">OpenWebUI (Timothy Jaeryang Baek)</a
				>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
	list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
	this list of conditions and the following disclaimer in the documentation
	and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
	contributors may be used to endorse or promote products derived from
	this software without specific prior written permission.

4. Notwithstanding any other provision of this License, and as a material condition of the rights granted herein, licensees are strictly prohibited from altering, removing, obscuring, or replacing any "OpenWebUI" branding, including but not limited to the name, logo, or any visual, textual, or symbolic identifiers that distinguish the software and its interfaces, in any deployment or distribution, regardless of the number of users, except as explicitly set forth in Clauses 5 and 6 below.

5. The branding restriction enumerated in Clause 4 shall not apply in the following limited circumstances: (i) deployments or distributions where the total number of end users (defined as individual natural persons with direct access to the application) does not exceed fifty (50) within any rolling thirty (30) day period; (ii) cases in which the licensee is an official contributor to the codebase—with a substantive code change successfully merged into the main branch of the official codebase maintained by the copyright holder—who has obtained specific prior written permission for branding adjustment from the copyright holder; or (iii) where the licensee has obtained a duly executed enterprise license expressly permitting such modification. For all other cases, any removal or alteration of the "OpenWebUI" branding shall constitute a material breach of license.

6. All code, modifications, or derivative works incorporated into this project prior to the incorporation of this branding clause remain licensed under the BSD 3-Clause License, and prior contributors retain all BSD-3 rights therein; if any such contributor requests the removal of their BSD-3-licensed code, the copyright holder will do so, and any replacement code will be licensed under the project's primary license then in effect. By contributing after this clause's adoption, you agree to the project's Contributor License Agreement (CLA) and to these updated terms for all new contributions.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
</pre>
		</div>

		<div class="mt-2 text-xs text-gray-400 dark:text-gray-500">
			{$i18n.t('Created by')}
			<a
				class=" text-gray-500 dark:text-gray-300 font-medium"
				href="https://github.com/tjbck"
				target="_blank">Timothy J. Baek</a
			>
		</div>
	</div>
</div>
