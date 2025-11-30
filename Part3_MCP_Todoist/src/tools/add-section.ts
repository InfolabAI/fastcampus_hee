import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerAddSection(server: McpServer, api: TodoistApi) {
    server.tool(
        'add-section',
        'Add a section to a project in Todoist',
        { projectId: z.string(), name: z.string(), order: z.number().optional() },
        async ({ projectId, name, order }) => {
            const section = await api.addSection({ projectId, name, order })
            return {
                content: [{ type: 'text', text: JSON.stringify(section, null, 2) }],
            }
        },
    )
}
