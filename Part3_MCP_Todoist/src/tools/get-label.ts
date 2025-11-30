import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerGetLabel(server: McpServer, api: TodoistApi) {
    server.tool(
        'get-label',
        'Get a label from Todoist',
        { labelId: z.string() },
        async ({ labelId }) => {
            const label = await api.getLabel(labelId)
            return {
                content: [{ type: 'text', text: JSON.stringify(label, null, 2) }],
            }
        },
    )
}
