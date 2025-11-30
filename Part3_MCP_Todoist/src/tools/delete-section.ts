import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerDeleteSection(server: McpServer, api: TodoistApi) {
    server.tool(
        'delete-section',
        'Delete a section from a project in Todoist',
        { sectionId: z.string() },
        async ({ sectionId }) => {
            const success = await api.deleteSection(sectionId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Section ${sectionId} deleted`
                            : `Failed to delete section ${sectionId}`,
                    },
                ],
            }
        },
    )
}
