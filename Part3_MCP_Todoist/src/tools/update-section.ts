import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerUpdateSection(server: McpServer, api: TodoistApi) {
    server.tool(
        'update-section',
        'Update a section in Todoist',
        { sectionId: z.string(), name: z.string() },
        async ({ sectionId, name }) => {
            const section = await api.updateSection(sectionId, { name })
            return {
                content: [{ type: 'text', text: JSON.stringify(section, null, 2) }],
            }
        },
    )
}
