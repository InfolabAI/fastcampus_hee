import type { TodoistApi } from '@doist/todoist-api-typescript'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

export function registerDeleteProject(server: McpServer, api: TodoistApi) {
    server.tool(
        'delete-project',
        'Delete a project in Todoist',
        { projectId: z.string() },
        async ({ projectId }) => {
            const success = await api.deleteProject(projectId)
            return {
                content: [
                    {
                        type: 'text',
                        text: success
                            ? `Project ${projectId} deleted`
                            : `Failed to delete project ${projectId}`,
                    },
                ],
            }
        },
    )
}
