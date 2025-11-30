import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerRemoveSharedLabel(server: McpServer, api: TodoistApi) {
    server.tool(
        'remove-shared-label',
        'Remove shared label in Todoist',
        {
            name: z.string(),
        },
        async ({ name }) => {
            const success = await api.removeSharedLabel({ name })
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Shared label ${name} remove`
                            : `Failed to remove shared label ${name}`,
                    },
                ],
            }
        },
    )
}
