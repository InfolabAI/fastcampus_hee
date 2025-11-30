import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerGetSection(server: McpServer, api: TodoistApi) {
    server.tool(
        'get-section',
        'Get section details in Todoist',
        {
            sectionId: z.string(),
        },
        async ({ sectionId }) => {
            const section = await api.getSection(sectionId)
            return {
                content: [{ type: 'text', text: JSON.stringify(section, null, 2) }],
            }
        },
    )
}
